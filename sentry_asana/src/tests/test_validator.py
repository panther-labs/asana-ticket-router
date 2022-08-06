# pylint: disable=redefined-outer-name

from unittest import mock
import pytest
from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.serializer.containers import SerializerContainer
from ..common.components.logger.containers import LoggerContainer
from ..producer.components.validator.service import ValidatorService
from ..producer.components.validator.containers import ValidatorContainer


@pytest.fixture
def container() -> ValidatorContainer:
    """Validator Container overrides"""

    logger_container = LoggerContainer()
    serializer_container = SerializerContainer()

    # Need to provide a mock client for SecretsManager so it
    # doesn't complain about boto3 region not set.
    secretsmanager_container = SecretsManagerContainer(
        config={'secret_name': 'SENTRY_ASANA_SECRETS'},
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
    )
    secretsmanager_client_mock = mock.Mock()
    secretsmanager_client_mock.get_secret_value.return_value = {
        "SecretString": "{\"SENTRY_CLIENT_SECRET\": \"Some Private Key\", \"DATADOG_SECRET_TOKEN\": \"MySuperSecretString\" }"
    }
    secretsmanager_container.secretsmanager_client.override(
        secretsmanager_client_mock)

    container = ValidatorContainer(
        logger=LoggerContainer.logger,
        development=False,
        keys=secretsmanager_container.keys
    )
    return container


@pytest.mark.asyncio
async def test_validate_tokens(container: ValidatorContainer) -> None:
    """Test validating a sentry token"""
    service = await container.validator_service()  # type: ignore
    signature = '64634bbddfd3a1bb0d6360839371aa12ea16d785c7f94bb6f2eac7ed5f3d235c'  # hmac-sha256
    is_valid = await service.validate_sentry('Hello World', signature)
    assert is_valid is True

    # When in development mode, test that we bypass the signature check
    with container.development.override(True):
        # Reset our singleton and create a new one that takes the override
        container.validator_service.reset()
        service = await container.validator_service()  # type: ignore
        is_valid = await service.validate_sentry('Hello World', 'Bad Signature')
    assert is_valid is True

    """Test validating a datadog token"""
    container.validator_service.reset()
    service = await container.validator_service()  # type: ignore
    is_valid = await service.validate_datadog('MySuperSecretString')
    assert is_valid is True

    # When in development mode, test that we bypass the signature check
    with container.development.override(True):
        # Reset our singleton and create a new one that takes the override
        container.validator_service.reset()
        service = await container.validator_service()  # type: ignore
        is_valid = await service.validate_datadog('ThisIsTheWrongSecretString')
    assert is_valid is True
