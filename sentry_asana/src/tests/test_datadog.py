# pylint: disable=redefined-outer-name
# mypy: ignore-errors

from unittest.mock import Mock
import json
import os
import pytest

from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.serializer.containers import SerializerContainer
from ..common.components.logger.containers import LoggerContainer
from ..consumer.components.datadog.containers import DatadogContainer
from ..consumer.components.datadog.service import (
    DatadogService,
    make_datadog_asana_event,
)


DATADOG_EVENT_DETAIL = os.path.join(
    os.path.dirname(__file__), 'test_data', 'datadog_event_details.json'
)


@pytest.fixture
def container() -> DatadogContainer:
    """Datadog Container overrides"""

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
        "SecretString": "{\"DATADOG_API_KEY\": \"MyDatadogAPIKey\", \"DATADOG_APP_KEY\": \"MyDatadogAppKey\" }"
    }
    secretsmanager_container.secretsmanager_client.override(secretsmanager_client_mock)

    container = DatadogContainer(
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        keys=secretsmanager_container.keys,
    )

    return container


@pytest.mark.asyncio
async def test_get_event_details(container: DatadogContainer) -> None:
    """Test get_event_details method"""

    datadog_client_response = Mock()
    datadog_client_response.to_dict.return_value = {'foo': 'bar'}

    datadog_client_mock = Mock()
    datadog_client_mock.call_api.return_value = datadog_client_response

    with container.client.override(datadog_client_mock):
        service: DatadogService = await container.datadog_service()

        response = await service.get_event_details({'id': "123456789"})
        assert response == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_post_event_details(container: DatadogContainer) -> None:
    datadog_client_response = Mock()
    expected = {'status': 'ok', 'event': {}}
    fake_event = {'title': 'title', 'tags': ['foo', 'bar'], 'text': 'some_text'}
    datadog_client_response.to_dict.return_value = expected
    datadog_client_mock = Mock()
    datadog_client_mock.call_api.return_value = datadog_client_response
    with container.client.override(datadog_client_mock):
        service: DatadogService = await container.datadog_service()
        response = await service.post_event_details(fake_event)
        assert response == expected


def test_make_datadog_asana_event() -> None:
    with open(DATADOG_EVENT_DETAIL, 'rb') as details:
        data = details.read()
        json_data = json.loads(data)
        event_data = json_data['event']
        event = make_datadog_asana_event(event_data, 'somelink')
        assert 'monitor_id:77955227' in event.get('tags')
        assert 'event_source:asana' in event.get('tags')
        # event tags is a superset of event_data tags.
        assert set(event_data.get('tags')).intersection(event.get('tags'))
