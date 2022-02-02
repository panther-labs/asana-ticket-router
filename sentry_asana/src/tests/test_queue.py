# pylint: disable=redefined-outer-name

from logging import Logger
from unittest import mock

import pytest

from ..producer.components.queue.containers import QueueContainer
from ..producer.components.logger.containers import LoggerContainer


@pytest.fixture
def container() -> QueueContainer:
    """Queue Container overrides"""
    # pylint: disable=redefined-outer-name
    container = QueueContainer(
        config={
            "queue_url": "some queue url"
        },
        logger=LoggerContainer.logger
    )
    return container


@pytest.mark.asyncio
async def test_que_put(container: QueueContainer) -> None:
    """Test queue put"""
    sqs_client_mock = mock.Mock()
    sqs_client_mock.send_message.return_value = {
        'response': 'success'
    }

    with container.sqs_client.override(sqs_client_mock):
        service = container.queue_service()
        response = await service.put("test message")

    assert response == {
        'response': 'success'
    }
