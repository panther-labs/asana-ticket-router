# pylint: disable=redefined-outer-name
# mypy: ignore-errors

from unittest.mock import Mock, AsyncMock
import pytest
import os
import json
from aiohttp import ClientResponse, ClientResponseError

from ..common.components.entities.service import EngTeam
from consumer.components.asana.entities import PRIORITY, AsanaFields
from ..consumer.components.requests.containers import RequestsContainer
from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.serializer.containers import SerializerContainer
from ..common.components.logger.containers import LoggerContainer
from ..consumer.components.sentry.containers import SentryContainer
from ..consumer.components.sentry.service import (
    SentryService,
    get_sentry_task_priority,
    extract_sentry_fields,
)

SENTRY_ISSUE = os.path.join(os.path.dirname(__file__), 'test_data', 'sentry_issue.json')
SENTRY_EVENT = os.path.join(os.path.dirname(__file__), 'test_data', 'sentry_event.json')


def raise_except() -> Exception:
    raise ClientResponseError(request_info=None, history=None)  # type: ignore


@pytest.fixture
def container() -> SentryContainer:
    """Sectry Container overrides"""

    logger_container = LoggerContainer()
    serializer_container = SerializerContainer()

    # Need to provide a mock client for SecretsManager so it
    # doesn't complain about boto3 region not set.
    secretsmanager_container = SecretsManagerContainer(
        config={'secret_name': 'SENTRY_ASANA_SECRETS'},
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
    )
    secretsmanager_client_mock = Mock()
    secretsmanager_client_mock.get_secret_value.return_value = {
        "SecretString": "{\"SENTRY_PAT\": \"Some Sentry PAT\"}"
    }
    secretsmanager_container.secretsmanager_client.override(secretsmanager_client_mock)

    container = SentryContainer(
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        keys=secretsmanager_container.keys,
    )

    return container


@pytest.mark.asyncio
async def test_find_by_id(container: SentryContainer) -> None:
    """Test find_by_id"""

    response_mock = AsyncMock(ClientResponse)
    response_mock.json.return_value = {'foo': 'bar'}
    session_mock = AsyncMock()
    session_mock.request.return_value = response_mock

    requests_container = RequestsContainer(
        logger=LoggerContainer.logger,
        serializer=SerializerContainer.serializer_service,
        session=session_mock,
    )
    requests_service = requests_container.requests_service()

    with container.requests.override(requests_service):
        service: SentryService = await container.sentry_service()

        response = await service.find_by_id('some task id')
        assert response == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_find_by_id_exception(container: SentryContainer) -> None:
    """Test find_by_id exception"""

    response_mock = AsyncMock(ClientResponse)
    response_mock.raise_for_status.side_effect = raise_except
    session_mock = AsyncMock()
    session_mock.request.return_value = response_mock

    requests_container = RequestsContainer(
        logger=LoggerContainer.logger,
        serializer=SerializerContainer.serializer_service,
        session=session_mock,
    )
    requests_service = requests_container.requests_service()

    # Test with exception
    with container.requests.override(requests_service):
        service: SentryService = await container.sentry_service()

        with pytest.raises(ClientResponseError):
            response = await service.find_by_id('some task id')
            assert response is None


@pytest.mark.asyncio
async def test_add_link(container: SentryContainer) -> None:
    """Test add_link"""

    response_mock = AsyncMock(ClientResponse)
    response_mock.json.return_value = {'foo': 'bar'}
    session_mock = AsyncMock()
    session_mock.request.return_value = response_mock

    requests_container = RequestsContainer(
        logger=LoggerContainer.logger,
        serializer=SerializerContainer.serializer_service,
        session=session_mock,
    )
    requests_service = requests_container.requests_service()

    with container.requests.override(requests_service):
        service: SentryService = await container.sentry_service()

        response = await service.add_link('issue_id', 'asana_task_id')
        assert response == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_add_link_exception(container: SentryContainer) -> None:
    """Test add_link exception"""

    response_mock = AsyncMock(ClientResponse)
    response_mock.raise_for_status.side_effect = raise_except
    session_mock = AsyncMock()
    session_mock.request.return_value = response_mock

    requests_container = RequestsContainer(
        logger=LoggerContainer.logger,
        serializer=SerializerContainer.serializer_service,
        session=session_mock,
    )
    requests_service = requests_container.requests_service()

    # Test with exception
    with container.requests.override(requests_service):
        service: SentryService = await container.sentry_service()

        with pytest.raises(ClientResponseError):
            response = await service.add_link('issue_id', 'asana_task_id')
            assert response is None


@pytest.mark.asyncio
async def test_get_sentry_asana_link(container: SentryContainer) -> None:
    """Test get_sentry_asana_link exception: no plugins"""

    response_mock = AsyncMock(ClientResponse)
    # Set to a paylaod that triggers the first exception
    response_mock.json.return_value = {'foo': 'bar'}
    session_mock = AsyncMock()
    session_mock.request.return_value = response_mock

    requests_container = RequestsContainer(
        logger=LoggerContainer.logger,
        serializer=SerializerContainer.serializer_service,
        session=session_mock,
    )
    requests_service = requests_container.requests_service()

    with container.requests.override(requests_service):
        service: SentryService = await container.sentry_service()

        with pytest.raises(ValueError):
            response = await service.get_sentry_asana_link('issue_id')
            assert str(ValueError) == 'Could not find any plugins for issue: (issue_id)'
            assert response is None

    # Next exception
    response_mock.json.return_value = {'pluginIssues': []}
    with pytest.raises(ValueError):
        response = await service.get_sentry_asana_link('issue_id')
        assert str(ValueError) == 'No asana plugin found for issue: (issue_id)'
        assert response is None

    # Test for no asana_link
    response_mock.json.return_value = {'pluginIssues': [{'id': 'asana'}]}
    response = await service.get_sentry_asana_link('issue_id')
    assert response is None

    # Test found asana_link
    response_mock.json.return_value = {
        'pluginIssues': [{'id': 'asana', 'issue': {'url': 'asana_url'}}]
    }
    response = await service.get_sentry_asana_link('issue_id')
    assert response == 'asana_url'


def test_get_sentry_task_priority() -> None:
    """Test _get_task_priority"""

    priority = get_sentry_task_priority('misc level')
    assert priority.name == PRIORITY.HIGH.name

    priority = get_sentry_task_priority('warning')
    assert priority == PRIORITY.MEDIUM


def test_extract_sentry_fields(investigations: EngTeam) -> None:
    """Test extract_sentry_fields"""

    with open(SENTRY_EVENT, encoding='utf-8') as file:
        data = json.load(file)
    fields = extract_sentry_fields(
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
        runbook_url='https://www.notion.so/pantherlabs/Sentry-issue-handling-ee187249a9dd475aa015f521de3c8396',
        routing_data='fake routing data',
    )


@pytest.fixture
def investigations() -> EngTeam:
    return EngTeam("investigations", "team", "backlog", "sprint", "sandbox", [])
