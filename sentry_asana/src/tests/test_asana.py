# pylint: disable=redefined-outer-name
import json
import os
from typing import Any, Dict, List
from unittest.mock import Mock
import pytest
from asana.error import ForbiddenError, NotFoundError
from consumer.components.asana.entities import (
    CUSTOMFIELD,
    PRIORITY,
    AsanaFields,
)
from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.serializer.containers import SerializerContainer
from ..common.components.logger.containers import LoggerContainer
from ..common.components.entities.service import EngTeam
from ..consumer.components.asana.containers import AsanaContainer
from ..consumer.components.asana.service import AsanaService
from ..common.constants import AlertType


ASANA_TASK = os.path.join(os.path.dirname(__file__), 'test_data', 'asana_task.json')
SENTRY_ISSUE = os.path.join(os.path.dirname(__file__), 'test_data', 'sentry_issue.json')
SENTRY_EVENT = os.path.join(os.path.dirname(__file__), 'test_data', 'sentry_event.json')
DATADOG_EVENT = os.path.join(
    os.path.dirname(__file__), 'test_data', 'datadog_event.json'
)


def raise_forbidden_except(*args: Any) -> Exception:
    raise ForbiddenError(*args)


def raise_not_found_except(*args: Any) -> Exception:
    raise NotFoundError(*args)


def mock_portfolio_data(id: str, **kargs: Any) -> List[Dict]:
    # We return a different list of projects based on
    # the input string for testing.
    if id == 'none':
        return []
    if id == 'filter':
        return [
            {
                "gid": "sprint_gid_2",
                "name": "Sprint: 2",
                "resource_type": "project",
                "archived": True,
                "created_at": "2022-01-02T00:00:00.000Z",
            },
            {
                "gid": "sprint_gid_3",
                "name": "Sprint: 3",
                "resource_type": "project",
                "archived": True,
                "created_at": "2022-01-03T00:00:00.000Z",
            },
        ]
    if id == 'release_board':
        return [
            {
                "gid": "release_gid_1",
                "name": "Release: 11",
                "resource_type": "project",
                "archived": False,
                "created_at": "2022-01-01T00:00:00.000Z",
            },
        ]
    return [
        {
            "gid": "sprint_gid_1",
            "name": "Sprint: 1",
            "resource_type": "project",
            "archived": False,
            "created_at": "2022-01-01T00:00:00.000Z",
        },
        {
            "gid": "sprint_gid_2",
            "name": "Sprint: 2",
            "resource_type": "project",
            "archived": True,
            "created_at": "2022-01-02T00:00:00.000Z",
        },
        {
            "gid": "sprint_gid_3",
            "name": "Sprint: 3",
            "resource_type": "project",
            "archived": False,
            "created_at": "2022-01-03T00:00:00.000Z",
        },
    ]


@pytest.fixture
def investigations() -> EngTeam:
    return EngTeam("investigations", "team", "backlog", "sprint", "sandbox", [])


@pytest.fixture
def observability() -> EngTeam:
    return EngTeam("Observability", "team", "backlog", "sprint", "sandbox", [])


@pytest.fixture
def asana_fields(investigations: EngTeam) -> AsanaFields:
    return AsanaFields(
        url='https://sentry.io/organizations/panther-labs/issues/2971136216',
        tags={
            'aws_account_id': '758312592604',
            'aws_org_id': 'o-wyibehgf3h',
            'aws_partition': 'aws',
            'aws_region': 'us-west-2',
            'commit_sha': '556d327fa',
            'data_lake': 'snowflake-self-hosted',
            'debug_enabled': 'false',
            'environment': 'dev',
            'fips_enabled': 'false',
            'lambda_memory_mb': '2048',
            'level': 'error',
            'os.name': 'linux',
            'runtime': 'go go1.17.1',
            'runtime.name': 'go',
            'server_name': 'panther-snowflake-api',
            'url': 'https://web-930307996.us-west-2.elb.amazonaws.com',
            'zap_lambdaRequestId': '3ad98716-cd00-41e2-af43-cb139bb969bb',
        },
        aws_region='us-west-2',
        aws_account_id='758312592604',
        customer='Unknown',
        display_name='Unknown',
        event_datetime='2022-01-29t00:19:22.986521z',
        environment='dev',
        title='snowflake-api: returned an error: AWS.ValidationException: cannot get snowflake secret: arn:aws:secretsmanager:us-west-2:758312592604:secret:panther-managed...',
        assigned_team=investigations,
        priority=PRIORITY.HIGH,
        project_gids=['sprint_gid_3', 'dev_board'],
        runbook_url='https://www.notion.so/pantherlabs/Sentry-issue-handling-ee187249a9dd475aa015f521de3c8396',
        routing_data='Fake Routing information',
    )


@pytest.fixture
def container() -> AsanaContainer:
    """Asana Container overrides"""

    logger_container = LoggerContainer()
    serializer_container = SerializerContainer()

    # Set our mocks for our asana client.
    portfolios_mock = Mock()
    portfolios_mock.get_items.side_effect = mock_portfolio_data

    tasks_mock = Mock()
    with open(ASANA_TASK, encoding='utf-8') as file:
        data = json.load(file)
        tasks_mock.find_by_id.return_value = data
        tasks_mock.create_task.return_value = {'gid': 'new_project_gid'}

    asana_client_mock = Mock()
    asana_client_mock.portfolios = portfolios_mock
    asana_client_mock.tasks = tasks_mock

    container = AsanaContainer(
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        asana_client=asana_client_mock,
        config={
            'is_lambda': "true",
            'debug': "false",
            'development': "false",
            'dev_asana_sentry_project': "dev_board",
            'release_testing_portfolio': "release_board",
        },
    )

    return container


@pytest.mark.asyncio
async def test_get_projects_in_portfolio(container: AsanaContainer) -> None:
    """Test _get_projects_in_portfolio"""

    service: AsanaService = container.asana_service()
    projects = await service._get_projects_in_portfolio('id')
    assert len(projects) == 3


@pytest.mark.asyncio
async def test_get_latest_project_id(container: AsanaContainer) -> None:
    """Test _get_latest_project_id"""

    service: AsanaService = container.asana_service()
    project_id = await service._get_latest_project_id('id')
    assert project_id == 'sprint_gid_3'

    # Test empty list as a result of filtering projects
    project_id = await service._get_latest_project_id('filter')
    assert project_id == None

    # Test empty list
    project_id = await service._get_latest_project_id('none')
    assert project_id == None


@pytest.mark.asyncio
async def test_get_dev_project_ids(container: AsanaContainer) -> None:
    """Test _get_dev_project_ids"""

    service: AsanaService = container.asana_service()
    project_ids = await service._get_dev_project_ids('id')
    assert project_ids == ['sprint_gid_3', 'dev_board']


@pytest.mark.asyncio
async def test_get_staging_project_ids(container: AsanaContainer) -> None:
    """Test _get_staging_project_ids"""

    service: AsanaService = container.asana_service()
    project_ids = await service._get_staging_project_ids('id')
    assert project_ids == ['sprint_gid_3', 'release_gid_1']

    # Test if all API calls returned nothing, that we at least assign
    # OBSERVABILITY_PERF backlog
    service._release_testing_portfolio = 'none'
    project_ids = await service._get_staging_project_ids('none')
    assert project_ids == [service.default_asana_portfolio_id]


@pytest.mark.asyncio
async def test_get_production_project_ids(container: AsanaContainer) -> None:
    """Test _get_production_project_ids"""

    service: AsanaService = container.asana_service()
    project_ids = await service._get_production_project_ids('id')
    assert project_ids == ['sprint_gid_3']

    project_ids = await service._get_production_project_ids('none')
    assert project_ids == [service.default_asana_portfolio_id]


@pytest.mark.asyncio
async def test_get_project_ids(
    container: AsanaContainer, observability: EngTeam
) -> None:
    """Test _get_project_ids"""

    service: AsanaService = container.asana_service()
    project_ids = await service._get_project_ids('dev', PRIORITY.MEDIUM, observability)
    assert project_ids == ['sprint_gid_3', 'dev_board']

    project_ids = await service._get_project_ids(
        'staging', PRIORITY.MEDIUM, observability
    )
    assert project_ids == ['sprint_gid_3', 'release_gid_1']

    project_ids = await service._get_project_ids('prod', PRIORITY.MEDIUM, observability)
    assert project_ids == ['backlog']

    project_ids = await service._get_project_ids('prod', PRIORITY.HIGH, observability)
    assert project_ids == ['sprint_gid_3']


@pytest.mark.asyncio
async def test_get_task_priority(container: AsanaContainer) -> None:
    """Test _get_task_priority"""

    service: AsanaService = container.asana_service()
    priority = service._get_task_priority('misc level', AlertType.SENTRY)
    assert priority.name == PRIORITY.HIGH.name

    priority = service._get_task_priority('warning', AlertType.SENTRY)
    assert priority == PRIORITY.MEDIUM

    priority = service._get_task_priority('p1', AlertType.DATADOG)
    assert priority.name == PRIORITY.HIGH.name

    priority = service._get_task_priority('p4', AlertType.DATADOG)
    assert priority == PRIORITY.MEDIUM


@pytest.mark.asyncio
async def test_extract_fields(
    container: AsanaContainer, investigations: EngTeam
) -> None:
    """Test _extract_fields"""

    service: AsanaService = container.asana_service()
    with open(SENTRY_EVENT, encoding='utf-8') as file:
        data = json.load(file)
    fields = await service.extract_sentry_fields(
        data['data']['event'], investigations, routing_data='fake routing data'
    )

    assert fields == AsanaFields(
        url='https://sentry.io/organizations/panther-labs/issues/2971136216',
        tags={
            'aws_account_id': '758312592604',
            'aws_org_id': 'o-wyibehgf3h',
            'aws_partition': 'aws',
            'aws_region': 'us-west-2',
            'commit_sha': '556d327fa',
            'data_lake': 'snowflake-self-hosted',
            'debug_enabled': 'false',
            'environment': 'dev',
            'fips_enabled': 'false',
            'lambda_memory_mb': '2048',
            'level': 'error',
            'os.name': 'linux',
            'runtime': 'go go1.17.1',
            'runtime.name': 'go',
            'server_name': 'panther-snowflake-api',
            'url': 'https://web-930307996.us-west-2.elb.amazonaws.com',
            'zap_lambdaRequestId': '3ad98716-cd00-41e2-af43-cb139bb969bb',
        },
        aws_region='us-west-2',
        aws_account_id='758312592604',
        customer='Unknown',
        display_name='Unknown',
        event_datetime='2022-01-29t00:19:22.986521z',
        environment='dev',
        title='snowflake-api: returned an error: AWS.ValidationException: cannot get snowflake secret: arn:aws:secretsmanager:us-west-2:758312592604:secret:panther-managed...',
        assigned_team=investigations,
        priority=PRIORITY.HIGH,
        project_gids=['sprint_gid_3', 'dev_board'],
        runbook_url='https://www.notion.so/pantherlabs/Sentry-issue-handling-ee187249a9dd475aa015f521de3c8396',
        routing_data='fake routing data',
    )


@pytest.mark.asyncio
async def test_create_task_note(
    container: AsanaContainer, asana_fields: AsanaFields
) -> None:
    """Test _create_task_note"""

    service: AsanaService = container.asana_service()
    note = service._create_task_note(asana_fields, None, None)
    assert (
        note
        == """Sentry Issue URL: https://sentry.io/organizations/panther-labs/issues/2971136216

Event Datetime: 2022-01-29t00:19:22.986521z

Customer Impacted: Unknown

Environment: dev

Runbook: https://www.notion.so/pantherlabs/Sentry-issue-handling-ee187249a9dd475aa015f521de3c8396

AWS Switch Role Link: https://us-west-2.signin.aws.amazon.com/switchrole?roleName=PantherSupportRole-us-west-2&account=758312592604&displayName=Unknown%20Support

Datadog Trace Link: https://app.datadoghq.com/apm/traces?query=@account_id:758312592604%20@request_id:3ad98716-cd00-41e2-af43-cb139bb969bb&start=1643411962986&historicalData=true

Routing Information: Fake Routing information

"""
    )
    # Test with root and previous asana links in the payload
    note = service._create_task_note(asana_fields, 'root_asana_link', 'prev_asana_link')
    assert (
        note
        == """Previous Asana Task: prev_asana_link

Root Asana Task: root_asana_link

Sentry Issue URL: https://sentry.io/organizations/panther-labs/issues/2971136216

Event Datetime: 2022-01-29t00:19:22.986521z

Customer Impacted: Unknown

Environment: dev

Runbook: https://www.notion.so/pantherlabs/Sentry-issue-handling-ee187249a9dd475aa015f521de3c8396

AWS Switch Role Link: https://us-west-2.signin.aws.amazon.com/switchrole?roleName=PantherSupportRole-us-west-2&account=758312592604&displayName=Unknown%20Support

Datadog Trace Link: https://app.datadoghq.com/apm/traces?query=@account_id:758312592604%20@request_id:3ad98716-cd00-41e2-af43-cb139bb969bb&start=1643411962986&historicalData=true

Routing Information: Fake Routing information

"""
    )


@pytest.mark.asyncio
async def test_create_task_body(
    container: AsanaContainer, asana_fields: AsanaFields
) -> None:
    """Test _create_task_body"""

    service: AsanaService = container.asana_service()
    body = service._create_task_body(asana_fields, 'some notes')
    assert body == {
        'name': asana_fields.title,
        'projects': asana_fields.project_gids,
        'custom_fields': {
            CUSTOMFIELD.PRIORITY.value: asana_fields.priority.value,
            CUSTOMFIELD.EPD_TASK_TYPE.value: CUSTOMFIELD.ON_CALL.value,
            CUSTOMFIELD.ESTIMATE.value: 0.1,  # Days
            CUSTOMFIELD.REPORTER.value: CUSTOMFIELD.SENTRY_IO.value,
            CUSTOMFIELD.TEAM.value: asana_fields.assigned_team.AsanaTeamId,
            CUSTOMFIELD.OUTCOME_FIELD.value: CUSTOMFIELD.OUTCOME_TYPE_KTLO.value,
        },
        'notes': 'some notes',
    }


@pytest.mark.asyncio
async def test_create_asana_task(
    container: AsanaContainer, asana_fields: AsanaFields
) -> None:
    """Test _create_asana_task"""

    service: AsanaService = container.asana_service()
    body = {
        'name': asana_fields.title,
        'projects': asana_fields.project_gids,
        'custom_fields': {
            CUSTOMFIELD.PRIORITY.value: asana_fields.priority.value,
            CUSTOMFIELD.EPD_TASK_TYPE.value: CUSTOMFIELD.ON_CALL.value,
            CUSTOMFIELD.ESTIMATE.value: 0.1,  # Days
            CUSTOMFIELD.REPORTER.value: CUSTOMFIELD.SENTRY_IO.value,
            CUSTOMFIELD.TEAM.value: asana_fields.assigned_team.AsanaTeamId,
            CUSTOMFIELD.OUTCOME_FIELD.value: CUSTOMFIELD.OUTCOME_TYPE_KTLO.value,
        },
        'notes': 'some notes',
    }
    response = await service._create_asana_task(body)
    assert response['gid'] == 'new_project_gid'


@pytest.mark.asyncio
async def test_create_task_from_sentry(
    container: AsanaContainer, observability: EngTeam
) -> None:
    """Test create_task"""

    service: AsanaService = container.asana_service()
    with open(SENTRY_EVENT, encoding='utf-8') as file:
        data = json.load(file)

    asana_fields: AsanaFields = await service.extract_sentry_fields(
        data['data']['event'],
        observability,
        routing_data='',
    )
    response = await service.create_task(asana_fields, None, None)
    assert response == 'new_project_gid'


@pytest.mark.asyncio
async def test_create_task_from_datadog(
    container: AsanaContainer, observability: EngTeam
) -> None:
    """Test create_task"""

    service: AsanaService = container.asana_service()
    with open(DATADOG_EVENT, encoding='utf-8') as file:
        data = json.load(file)

    asana_fields: AsanaFields = await service.extract_datadog_fields(
        data,
        observability,
        routing_data='',
    )

    # We aren't actually doing this in the code yet, but we will.
    response = await service.create_task(asana_fields, None, None)
    assert response == 'new_project_gid'


@pytest.mark.asyncio
async def test_find_asana_task(container: AsanaContainer) -> None:
    """Test _find_asana_task"""

    service: AsanaService = container.asana_service()
    response = await service._find_asana_task('some task gid')

    with open(ASANA_TASK, encoding='utf-8') as file:
        data = json.load(file)
    assert response == data

    # Next, test that exception is caught safely and returns None
    tasks_mock = Mock()
    tasks_mock.find_by_id.side_effect = raise_forbidden_except
    asana_client_mock = Mock()
    asana_client_mock.tasks = tasks_mock
    with container.asana_client.override(asana_client_mock):
        # reset the singleton
        container.asana_service.reset()
        service = container.asana_service()
        response = await service._find_asana_task('some task gid')
        assert response is None

    # Test not found exception
    tasks_mock.find_by_id.side_effect = raise_not_found_except
    with container.asana_client.override(asana_client_mock):
        # reset the singleton
        container.asana_service.reset()
        service = container.asana_service()
        response = await service._find_asana_task('some task gid')
        assert response is None


@pytest.mark.asyncio
async def test_extract_root_asana_link(container: AsanaContainer) -> None:
    """Test extract_root_asana_link"""

    # Test if Forbidden, (None response back from API handler)
    tasks_mock = Mock()
    tasks_mock.find_by_id.side_effect = raise_forbidden_except
    asana_client_mock = Mock()
    asana_client_mock.tasks = tasks_mock
    with container.asana_client.override(asana_client_mock):
        # reset the singleton
        container.asana_service.reset()
        service = container.asana_service()
        response = await service.extract_root_asana_link('some task gid')
        assert response is None

    # Test if Not Found, (None reponse back from API handler)
    tasks_mock.find_by_id.side_effect = raise_not_found_except
    with container.asana_client.override(asana_client_mock):
        # reset the singleton
        container.asana_service.reset()
        service = container.asana_service()
        response = await service.extract_root_asana_link('some task gid')
        assert response is None

    # Test if 'notes' attribute exists
    tasks_mock.find_by_id.side_effect = None
    tasks_mock.find_by_id.return_value = {"foo": "bar"}
    response = await service.extract_root_asana_link('some task gid')
    assert response == None

    # Test if regex 'search' failed on the `Root Asana Task`
    tasks_mock.find_by_id.return_value = {"notes": "foobar"}
    response = await service.extract_root_asana_link('some task gid')
    assert response == None

    # Test successful URL parsing
    tasks_mock.find_by_id.return_value = {
        "notes": "Root Asana Task: https://app.asana.com/1/2/3"
    }
    response = await service.extract_root_asana_link('some task gid')
    assert response == 'https://app.asana.com/1/2/3'


@pytest.mark.asyncio
async def tests_asana_client() -> None:
    """Test asana_client loads proper dependencies"""

    logger_container = LoggerContainer()
    serializer_container = SerializerContainer()

    # Need to provide a mock client for SecretsManager
    secretsmanager_container = SecretsManagerContainer(
        config={'secret_name': 'SENTRY_ASANA_SECRETS'},
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
    )
    secretsmanager_client_mock = Mock()
    secretsmanager_client_mock.get_secret_value.return_value = {
        "SecretString": "{\"ASANA_PAT\": \"Some Asana PAT\"}"
    }
    secretsmanager_container.secretsmanager_client.override(secretsmanager_client_mock)

    container = AsanaContainer(
        config={
            'development': 'false',
            'dev_asana_sentry_project': '123',
            'release_testing_portfolio': '123',
        },
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        keys=secretsmanager_container.keys,
    )

    # Must await because we depend on the mocked secrets manager's keys
    service = await container.asana_service()  # type: ignore
    assert isinstance(service, AsanaService)
