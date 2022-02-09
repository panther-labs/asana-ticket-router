# pylint: disable=redefined-outer-name

from unittest.mock import Mock

import pytest
from requests import Response
from ..common.components.logger.containers import LoggerContainer
from ..consumer.components.requests.containers import RequestsContainer
from ..consumer.components.requests.service import RequestsService


@pytest.fixture
def container() -> RequestsContainer:
    """Requests Container overrides"""

    logger_container = LoggerContainer()

    requests_client_mock = Mock()
    mock_response = Mock(Response)
    mock_response.json.return_value = {'foo': 'bar'}
    requests_client_mock.request.return_value = mock_response

    container = RequestsContainer(
        logger=logger_container.logger,
        requests_client=requests_client_mock
    )
    return container


@pytest.mark.asyncio
async def test_request(container: RequestsContainer) -> None:
    """Test making a POST request"""

    service: RequestsService = container.requests_service()

    payload = {'foo': 'bar'}
    response = await service.request('POST', 'https://panther.io', json=payload)

    assert service._client.request.called, 'Should have been called'
    service._client.request.assert_called_once_with(
        'POST',
        'https://panther.io',
        json=payload
    )

    assert isinstance(response, Response)
    assert response.json() == payload
