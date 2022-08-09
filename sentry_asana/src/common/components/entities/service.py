# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

from __future__ import annotations

import functools
import re
from typing import Annotated, Optional, List
import dataclasses
import dataclass_wizard


class TeamServiceException(BaseException):
    """Team service failed."""


@dataclasses.dataclass
class Matcher(dataclass_wizard.YAMLWizard):
    """Top level class for Matchers"""

    Key: str  # pylint: disable=invalid-name
    Value: str | None  # pylint: disable=invalid-name

    def __init__(self, chars: str):
        self.Key = chars
        self.Value = None
        if ":" in chars:
            self.Key, self.Value = chars.split(":", 1)

        self._regexp = False
        if self.Value is not None:
            self._regexp = self.Value.startswith("/") and self.Value.endswith("/")
            if self._is_regexp_value():
                # Chop off the leading and trailing / to get the real regexp.
                self.Value = self.Value[1:-1]

    def _is_regexp_value(self) -> bool:
        """Is this matcher's value a regexp."""
        return self._regexp

    def match(self, resource: dict) -> bool:
        """Does this matcher match resource?"""
        if self._is_regexp_value():
            return self.Key in resource and bool(
                re.search(self.Value, resource[self.Key])
            )
        return self.Key in resource and resource[self.Key] == self.Value


@dataclasses.dataclass
class EntityMatcher(dataclass_wizard.YAMLWizard):
    """EntityMatcher enables Teams to declare ownership over entities through the use of tags.
    - EntityMatchers are just a series of tags AND'd together.
    - An entity will match IFF its tags match *all* of the tags in this matcher.
    - An entityMatcher with an empty tags list matches no entities.
    """

    # This matches stuff basically lets users pass in strings, and we convert the strings to concrete matchers at serialization time.
    Matchers: Annotated[  # pylint: disable=invalid-name
        list[str] | list[Matcher], dataclasses.field(default=list)
    ]

    @property  # type: ignore # we redefined Matchers intentionally.
    def Matchers(self) -> list[Matcher]:  # pylint: disable=invalid-name
        """Matchers property, matchers.setter, and the annotations are a yamlwizard workaround.
        https://pypi.org/project/dataclass-wizard/#usage-and-examples
        This construct lets us use list[str] in YAML (to ease development) and convert to list[Matchers] in the code.
        """
        return self._matchers

    @Matchers.setter
    def Matchers(  # pylint: disable=invalid-name
        self, matchers: list[Matcher] | list[str]
    ) -> None:
        # Convert from strings to Matcher objects; if necessary.
        self._matchers: list[Matcher] = [
            Matcher(m) if isinstance(m, str) else m for m in matchers
        ]

    @dataclasses.dataclass
    class MatchResult:
        """MatchResult is just a named tuple, basically."""
        # Number of matches
        Count: int  # pylint: disable=invalid-name
        # When more than one matcher matches an entity, we use Precedence to rank and break ties.
        Precedence: int  # pylint: disable=invalid-name

    def __hash__(self) -> int:
        """EntityMatchers must be hashable to be a dict key or set item."""
        return hash(self.tags)

    @functools.cache
    def tags(self) -> dict:
        """Helper for __hash__."""
        return dict((m.Key, m.Value) for m in self._matchers)

    @functools.cache
    def precedence(self) -> int:
        """Precedence returns the precedence of this matcher; it affects how matches are ranked.

        We prefer specific tags like 'team' and 'service' more strongly over other tags.
        """
        if "team" in self.tags():
            return 3
        if "service" in self.tags():
            return 2
        return 1

    def match_rank(self, resource: dict) -> Optional[MatchResult]:
        """match_rank returns the number of tags that matched this entity to a resource."""
        try:
            matches = [m for m in self._matchers if m.match(resource)]
            if matches:
                return EntityMatcher.MatchResult(len(matches), self.precedence())
        except KeyError:
            pass
        return None

@dataclasses.dataclass
class EngTeam(dataclass_wizard.YAMLWizard):
    """EngTeam contains Asana queue information for a team, as well as what Entities they own."""

    # See data/teams.yaml for more complete documentation.
    Name: str
    AsanaTeamId: str
    AsanaBacklogId: str
    AsanaSprintPortfolioId: str
    Entities: list[EntityMatcher]

class TeamService:
    """Team Services offers APIs around Team's and entities, including relations."""

    DefaultTeamKey = "Observability"  # should be in the input.

    def __init__(
        self,
        team_data: str,
    ):
        self.teams: List[EngTeam] = []
        try:

            self._load(team_data)
            self._validate()
        except (ValueError, TypeError) as ex:
            raise TeamServiceException from ex

    def _validate(self) -> bool:
        return self._validate_default_team()

    def _validate_default_team(self) -> bool:
        for team in self.get_teams():
            if team.Name == TeamService.DefaultTeamKey:
                return True
        raise TeamServiceException(
            f"Failed to validate teams data, missing Service: {TeamService.DefaultTeamKey}"
        )

    def _load(self, team_data: str) -> None:
        """Load from yaml into self.teams and self.services."""
        self.teams = EngTeam.from_yaml(team_data)

    def get_teams(self) -> List[EngTeam]:
        """Returns an iterable of the teams in this service."""
        return self.teams

    def get_team(self, team_name: str) -> Optional[EngTeam]:
        """Public API to get an EngTeam given a team name."""
        return self._get_eng_team(team_name)

    def _get_eng_team(self, name: str) -> Optional[EngTeam]:
        """A helper for iterable traversal; returns empty list if missing."""
        for team in self.teams:
            if team.Name == name:
                return team
        return None

    def default_team(self) -> EngTeam:
        """Returns the default EngTeam."""
        team = self._get_eng_team(TeamService.DefaultTeamKey)
        if team:
            return team
        # _Validate would have raised if DefaultTeam did not exist, so we can just raise here.
        raise TeamServiceException
