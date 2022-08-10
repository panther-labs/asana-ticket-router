# pylint: disable=redefined-outer-name

from unittest.mock import AsyncMock
import pytest
from aiohttp import ClientResponse, ClientSession
from ..common.components.logger.containers import LoggerContainer
from ..common.components.serializer.containers import SerializerContainer
from ..consumer.components.requests.containers import RequestsContainer
from ..consumer.components.requests.service import RequestsService


@pytest.fixture
def container_with_mock() -> RequestsContainer:
    """Requests Container with mocked session"""

    response_mock = AsyncMock(ClientResponse)
    response_mock.json.return_value = {'foo': 'bar'}
    session_mock = AsyncMock()
    session_mock.request.return_value = response_mock

    container = RequestsContainer(
        logger=LoggerContainer().logger,
        serializer=SerializerContainer.serializer_service,
        session=session_mock,
    )
    return container


@pytest.fixture
def container() -> RequestsContainer:
    """Requests Container with no session"""

    return RequestsContainer(
        logger=LoggerContainer().logger,
        serializer=SerializerContainer.serializer_service,
        session=None,
    )


@pytest.mark.asyncio
async def test_request(container_with_mock: RequestsContainer) -> None:
    """Test making a request"""

    service: RequestsService = container_with_mock.requests_service()
    payload = {'foo': 'bar'}
    response = await service.request('POST', 'https://asdf.io', json=payload)
    assert service._session is not None
    assert service._session.request.called, 'Should have been called'  # type: ignore
    service._session.request.assert_called_once_with(  # type: ignore
        'POST', 'https://asdf.io', json=payload
    )

    assert isinstance(response, ClientResponse)
    jsn = await response.json()
    assert jsn == payload


@pytest.mark.asyncio
async def test_with_session(container: RequestsContainer) -> None:
    """Test using an async session context"""
    service: RequestsService = container.requests_service()

    assert service._session is None

    # Test empty session raises an error
    with pytest.raises(RuntimeError) as ex:
        await service.request('POST', 'https://panther.io', json={})

    async with service.with_session():
        assert isinstance(service._session, ClientSession)

    assert service._session is None
