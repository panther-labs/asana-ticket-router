# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=invalid-name

from typing import List
from logging import Logger
import dataclasses
import dataclass_wizard


@dataclasses.dataclass
class EngTeam(dataclass_wizard.YAMLWizard):
    """EngTeam contains Asana queue information for a team."""

    Name: str
    Email: str
    AsanaTeamId: str
    AsanaBacklogId: str
    AsanaSprintId: str


@dataclasses.dataclass
class Service(dataclass_wizard.YAMLWizard):
    """Service contains a service definition."""

    # The name of your service.
    Name: str
    # A short one line description of your service.
    Description: str
    # Should be a valid team in teams.yaml
    Team: str
    # Link to notion, ideally.
    Url: str
    # A list of URLMaps for this service.
    Urlmaps: list[str] = dataclasses.field(default_factory=list)
    # A list of other services, that this service is composed of
    Services: list[str] = dataclasses.field(default_factory=list)
    # A list of lambdas that this service is composed of
    Lambdas: list[str] = dataclasses.field(default_factory=list)


class TeamServiceException(BaseException):
    """Team service failed."""


class TeamService:
    """Team Service."""

    DefaultServiceKey = "CatchAllService"  # should be in the input.

    def __init__(
        self,
        logger: Logger,
    ):
        self._logger = logger
        self.teams: List[EngTeam] = []
        self.services: List[Service] = []
        self._Load()
        if not self._Validate():
            raise TeamServiceException

    def _Validate(self) -> bool:
        for service in self.services:
            if service.Name == TeamService.DefaultServiceKey:
                return True

        return False

    def _Load(self) -> None:
        """Load from yaml into self.teams and self.services."""
        with open(
            "sentry_asana/src/common/components/entities/data/teams.yaml", "rb"
        ) as teams_file:
            self.teams = EngTeam.from_yaml_file(teams_file.name)
        with open(
            "sentry_asana/src/common/components/entities/data/services.yaml", "rb"
        ) as services_file:
            self.services = Service.from_yaml_file(services_file.name)

    def GetTeams(self) -> List[EngTeam]:
        """Returns an iterable of the teams in this service."""
        return self.teams

    def _getService(self, service: str) -> List[Service]:
        """A helper for iterable traversal; returns empty list if missing."""
        return [s for s in self.services if s.Name == service]

    def _getEngTeam(self, team: str) -> List[EngTeam]:
        """A helper for iterable traversal; returns empty list if missing."""
        return [t for t in self.teams if t.Name == team]

    def DefaultService(self) -> List[Service]:
        """Returns the default service or empty iterable."""
        return self._getService(TeamService.DefaultServiceKey)

    def GetTeamForService(self, service: str) -> List[EngTeam]:
        """Returns the EngTeam for a service, or [] on error."""
        result = self._getService(service)
        if result:
            return self._getEngTeam(result[0].Team)
        return []
