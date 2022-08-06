import io
import pytest
from sentry_asana.src.common.components.entities import heuristics

from sentry_asana.src.common.components.entities.service import TeamService
from sentry_asana.src.common.components.entities.containers import EntitiesContainer

def team_data_file() -> io.StringIO:
  return io.StringIO("""
---
  - 
    Name: "Observability"
    Email: "team-platform-observability@panther.io"
    AsanaTeamId: "1201305154831712"
    AsanaBacklogId: "1201267919523642"
    AsanaSprintPortfolioId: "1201680804234024"
    Entities: [
      Tags: ["services:sentry2asana"],
      Tags: ["foo"],
    ]
  """)

@pytest.fixture
def container_with_mock() -> EntitiesContainer:
  return EntitiesContainer(
    config={
      'entities': {
        'team_data_file': team_data_file(),
      },
    })

@pytest.fixture
def container_with_data() -> EntitiesContainer:
  return EntitiesContainer(
    config={
      'entities': {
         'team_data_file': 'sentry_asana/src/tests/test_data/teams_test.yaml'
      },
    })

def test_TeamServiceInit(container_with_mock: EntitiesContainer) -> None:
  teams_service: TeamService = container_with_mock.teams_service()
  assert teams_service.DefaultTeam() != [], ""

def test_TeamServiceAccessors(container_with_mock: EntitiesContainer) -> None:
  teams_service: TeamService = container_with_mock.teams_service()
  teams = teams_service.GetTeams()
  assert len(teams) != 0
  assert teams[0].Name == 'Observability'

def test_ResourceMatcher(container_with_data: EntitiesContainer) -> None:
  teams_service: TeamService = container_with_data.teams_service()
  
  entity = {'service':'panther-lambda-func'}
  assert heuristics.GetTeam(teams_service, entity).Name == 'TestTeam'

  # Ensure precedence prefers team tag over service tag.
  entity = {'service':'panther-lambda-func','team': 'foo'}
  assert heuristics.GetTeam(teams_service, entity).Name == 'OtherTeam'

  # Ensure entities with no matches get default team assignment.
  entity = {'this-is-not-a-real-tag': None} # type: ignore
  assert heuristics.GetTeam(teams_service, entity).Name == 'Observability'