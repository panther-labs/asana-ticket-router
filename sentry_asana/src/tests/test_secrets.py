# pylint: disable=redefined-outer-name

from unittest import mock

import pytest
from ..producer.components.secrets.containers import SecretsManagerContainer
from ..producer.components.logger.containers import LoggerContainer
from ..producer.components.serializer.containers import SerializerContainer


@pytest.fixture
def container() -> SecretsManagerContainer:
    """Secrets Container overrides"""
    # pylint: disable=redefined-outer-name
    container = SecretsManagerContainer(
        config={
            "secret_name": "some secret name"
        },
        logger=LoggerContainer.logger,
        serializer=SerializerContainer.serializer_service
    )
    return container


@pytest.mark.asyncio
async def test_get_secret(container: SecretsManagerContainer) -> None:
    """Test getting a secret"""
    secretsmanager_client_mock = mock.Mock()
    secretsmanager_client_mock.get_secret_value.return_value = {
        "SecretString": "{\"SECRET_KEY\": \"SECRET_VALUE\"}"
    }

    with container.secretsmanager_client.override(secretsmanager_client_mock):
        service = container.secretsmanager_service()

    aws_secret = await service.get_secret()
    assert aws_secret == {
        "SecretString": "{\"SECRET_KEY\": \"SECRET_VALUE\"}"
    }


@pytest.mark.asyncio
async def test_get_secret_string(container: SecretsManagerContainer) -> None:
    """Test getting a secret"""
    secretsmanager_client_mock = mock.Mock()
    secretsmanager_client_mock.get_secret_value.return_value = {
        "SecretString": "{\"SECRET_KEY\": \"SECRET_VALUE\"}"
    }

    with container.secretsmanager_client.override(secretsmanager_client_mock):
        service = container.secretsmanager_service()

    secret_string = await service.get_secret_string()
    assert secret_string == {"SECRET_KEY": "SECRET_VALUE"}


@pytest.mark.asyncio
async def test_get_key(container: SecretsManagerContainer) -> None:
    """Test getting a secret"""
    secretsmanager_client_mock = mock.Mock()
    secretsmanager_client_mock.get_secret_value.return_value = {
        "SecretString": "{\"SECRET_KEY\": \"SECRET_VALUE\"}"
    }

    with container.secretsmanager_client.override(secretsmanager_client_mock):
        service = container.secretsmanager_service()

    key = await service.get_key('SECRET_KEY')
    assert key == 'SECRET_VALUE'

    # Test cached key
    key = await service.get_key('SECRET_KEY')
    assert key == 'SECRET_VALUE'
