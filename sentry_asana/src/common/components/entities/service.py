# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=invalid-name

import functools
import itertools

from typing import List, Optional, Dict, Any
import dataclasses
import dataclass_wizard


class TeamServiceException(BaseException):
    """Team service failed."""

@dataclasses.dataclass
class EntityMatcher(dataclass_wizard.YAMLWizard):
    """EntityMatcher enables Teams to declare ownership over entities through the use of tags.
     - Only one team can own a given entity.
     - EntityMatchers are just a series of tags AND'd together.
     - An entity will match IFF its tags match *all* of the tags in this matcher.
     - An entityMatcher with an empty tags list matches no entities.
     - Currently only exact matches are allowed.
     - Its disallowed to duplicate an EntityMatcher (because it might allow 2 teams to own a given entity.)
    """
    Tags: list[str]

    @dataclasses.dataclass
    class MatchResult:
        """MatchResult is just a named tuple, basically."""
        # Number of matches
        Count: int
        # When more than one matcher matches an entity, we use Precedence to rank and break ties.
        Precedence: int

    def __hash__(self) -> int:
        """EntityMatcher needs to have unique tags across all instances, so to enforce this, it must be hashable."""
        return hash("".join(self.Tags))

    @functools.cache
    def _tags(self) -> dict:
        return dict(
            tuple(tag.split(":", 1)) # type: ignore
            if ":" in tag else (tag, None)
            for tag in self.Tags
        )

    @functools.cache
    def Precedence(self) -> int:
        """Precedence returns the precedence of this matcher; it affects how matches are ranked.

        We prefer specific tags like 'team' and 'service' more strongly over other tags.
        """
        if "team" in self._tags():
            return 3
        if "service" in self._tags():
            return 2
        return 1

    def MatchRank(self, resource: dict) -> Optional[MatchResult]:
        """MatchRank returns the number of tags that matched this entity to a resource."""
        try:
            matches = {
                k: v for k, v in self._tags().items() if k in resource and resource[k] == v
            }
            if matches:
                return EntityMatcher.MatchResult(len(matches), self.Precedence())
        except KeyError:
            pass
        return None

@dataclasses.dataclass
class EngTeam(dataclass_wizard.YAMLWizard):
    """EngTeam contains Asana queue information for a team, as well as what Entities they own."""

    # See data/teams.yaml for more complete documentation.
    Name: str
    Email: str
    AsanaTeamId: str
    AsanaBacklogId: str
    AsanaSprintId: str
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
            self._Load(team_data)
            self._Validate()
        except (ValueError, TypeError) as e:
            raise TeamServiceException from e

    def _Validate(self) -> bool:
        return (
            self._ValidateDefaultTeamIsPresent() and self._EnsureUniqueEntityMatchers()
        )

    def _EnsureUniqueEntityMatchers(self) -> bool:
        """Ensure that each Team has all unique EntityMatchers; globally for all teams."""
        seen: Dict[int, Any] = {}
        entities = [t.Entities for t in self.GetTeams()]
        for matcher in itertools.chain(*entities):
            h = hash(matcher)
            if h in seen:
                # TODO: Add more information here.
                return False
            seen[h] = None
        return True

    def _ValidateDefaultTeamIsPresent(self) -> bool:
        for t in self.GetTeams():
            if t.Name == TeamService.DefaultTeamKey:
                return True
        raise TeamServiceException(
            f"Failed to validate teams data, missing Service: {TeamService.DefaultTeamKey}"
        )

    def _Load(self, team_data: str) -> None:
        """Load from yaml into self.teams and self.services."""
        self.teams = EngTeam.from_yaml(team_data)

    def GetTeams(self) -> List[EngTeam]:
        """Returns an iterable of the teams in this service."""
        return self.teams

    def GetTeam(self, teamName: str) -> Optional[EngTeam]:
        """Public API to get an EngTeam given a team name."""
        return self._getEngTeam(teamName)

    def _getEngTeam(self, name: str) -> Optional[EngTeam]:
        """A helper for iterable traversal; returns empty list if missing."""
        for t in self.teams:
            if t.Name == name:
                return t
        return None

    def DefaultTeam(self) -> EngTeam:
        """Returns the default EngTeam."""
        team = self._getEngTeam(TeamService.DefaultTeamKey)

        if team:
            return team
        # _Validate would have raised if DefaultTeam did not exist, so we can just raise here.
        raise TeamServiceException
