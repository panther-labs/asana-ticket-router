# pylint: disable=redefined-outer-name
# mypy: ignore-errors

from unittest.mock import Mock, AsyncMock
import pytest
from aiohttp import ClientResponse, ClientResponseError

from ..consumer.components.requests.containers import RequestsContainer
from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.serializer.containers import SerializerContainer
from ..common.components.logger.containers import LoggerContainer
from ..consumer.components.sentry.containers import SentryContainer
from ..consumer.components.sentry.service import SentryService


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
    secretsmanager_container.secretsmanager_client.override(
        secretsmanager_client_mock)

    container = SentryContainer(
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        keys=secretsmanager_container.keys
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
            assert str(
                ValueError) == 'Could not find any plugins for issue: (issue_id)'
            assert response is None

    # Next exception
    response_mock.json.return_value = {'pluginIssues': []}
    with pytest.raises(ValueError):
        response = await service.get_sentry_asana_link('issue_id')
        assert str(
            ValueError) == 'No asana plugin found for issue: (issue_id)'
        assert response is None

    # Test for no asana_link
    response_mock.json.return_value = {
        'pluginIssues': [
            {
                'id': 'asana'
            }
        ]
    }
    response = await service.get_sentry_asana_link('issue_id')
    assert response is None

    # Test found asana_link
    response_mock.json.return_value = {
        'pluginIssues': [
            {
                'id': 'asana',
                'issue': {
                    'url': 'asana_url'
                }
            }
        ]
    }
    response = await service.get_sentry_asana_link('issue_id')
    assert response == 'asana_url'
