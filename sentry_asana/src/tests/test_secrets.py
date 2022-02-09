# pylint: disable=redefined-outer-name

from unittest import mock

import pytest
from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.logger.containers import LoggerContainer
from ..common.components.serializer.containers import SerializerContainer


@pytest.fixture
def container() -> SecretsManagerContainer:
    """Secrets Container overrides"""

    secretsmanager_client_mock = mock.Mock()
    secretsmanager_client_mock.get_secret_value.return_value = {
        "SecretString": "{\"SECRET_KEY\": \"SECRET_VALUE\"}"
    }

    container = SecretsManagerContainer(
        config={
            "secret_name": "some secret name"
        },
        logger=LoggerContainer.logger,
        serializer=SerializerContainer.serializer_service,
        secretsmanager_client=secretsmanager_client_mock
    )
    return container


@pytest.mark.asyncio
async def test_get_secret_string(container: SecretsManagerContainer) -> None:
    """Test getting a secret"""
    service = container.secretsmanager_service()
    secret_string = await service.get_secret_string()
    assert secret_string == {"SECRET_KEY": "SECRET_VALUE"}
