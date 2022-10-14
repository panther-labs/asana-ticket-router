import io
import pytest

from common.components.entities import heuristics
from common.components.entities.service import TeamService, Matcher
from common.components.entities.containers import EntitiesContainer
import os


TEAMS_TEST_YAML = os.path.join(
    os.path.dirname(__file__), 'test_data', 'teams_test.yaml'
)
TEAMS_PROD_YAML = os.path.join(
    os.path.dirname(__file__),
    '..',
    'common',
    'components',
    'entities',
    'data',
    'teams.yaml',
)


def team_data_file() -> io.StringIO:
    return io.StringIO(
        """
---
  - 
    Name: "Observability and Performance"
    AsanaTeamId: "1201305154831712"
    AsanaBacklogId: "1201267919523642"
    AsanaSprintPortfolioId: "1201680804234024"
    AsanaSandboxPortfolioId: "12345"
    Entities: [
      Matchers: ["service:sentry2asana"],
      Matchers: ["foo"],
    ]
  """
    )


@pytest.fixture
def container_with_mock() -> EntitiesContainer:
    return EntitiesContainer(
        config={
            "entities": {
                "team_data_file": team_data_file(),
            },
        }
    )


@pytest.fixture
def container_with_data() -> EntitiesContainer:
    return EntitiesContainer(
        config={
            "entities": {"team_data_file": TEAMS_TEST_YAML},
        }
    )


def test_TeamServiceInit(container_with_mock: EntitiesContainer) -> None:
    teams_service: TeamService = container_with_mock.teams_service()
    assert teams_service.default_team() != [], ""


def test_TeamServiceAccessors(container_with_mock: EntitiesContainer) -> None:
    teams_service: TeamService = container_with_mock.teams_service()
    teams = teams_service.get_teams()
    assert len(teams) != 0
    assert teams[0].Name == "Observability and Performance"


def test_ResourceMatcher(container_with_data: EntitiesContainer) -> None:
    teams_service: TeamService = container_with_data.teams_service()

    entity = {"service": "panther-lambda-func"}
    team, routing = heuristics.get_team(teams_service, entity)
    assert team.Name == "TestTeam"
    assert routing.Matches[0] == Matcher('service:panther-lambda-func')

    # Ensure precedence prefers team tag over service tag.
    entity = {"service": "panther-lambda-func", "team": "foo"}
    team, unused_result = heuristics.get_team(teams_service, entity)
    assert team.Name == "OtherTeam"

    # Ensure entities with no matches raise DefaultTeamException
    entity = {"this-is-not-a-real-tag": None}  # type: ignore
    with pytest.raises(heuristics.TeamNotFound):
        heuristics.get_team(teams_service, entity)

    # Ensure entities match on regexp matchers
    entity = {"url": "/some/panther/component"}
    team, routing = heuristics.get_team(teams_service, entity)
    assert team.Name == "OtherTeam"
    assert routing.Matches[0] == Matcher("url://some/")

    # Test slash in path
    # Ensure entities match on regexp matchers
    entity = {"url": "https://panther-tse.runpanther.net/settings/general/"}
    team, routing = heuristics.get_team(teams_service, entity)
    assert team.Name == "OtherTeam"
    assert routing.Matches[0] == Matcher('url://settings/general//')

    # test zap_prefix matching
    entity = {"zap_service": "panther-lambda-func"}
    team, routing = heuristics.get_team(teams_service, entity)
    assert team.Name == "TestTeam"
    assert routing.Matches[0] == Matcher('service:panther-lambda-func')


def test_prod_config() -> None:
    teams_service = EntitiesContainer(
        config={
            'entities': {
                'team_data_file': TEAMS_PROD_YAML,
            },
        }
    ).teams_service()
    entity = {"server_name": "panther-datacatalog-updater"}
    team, unused_routing_data = heuristics.get_team(teams_service, entity)
    assert team.Name == 'Investigations'
