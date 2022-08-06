# pylint: disable=redefined-outer-name
import pytest
from unittest import mock
from ..common.components.secrets.service import SecretsManagerService
from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.serializer.service import SerializerService
from ..common.components.serializer.containers import SerializerContainer
from ..common.components.logger.service import LoggerService
from ..common.components.logger.containers import LoggerContainer
from ..producer.components.application import ApplicationContainer
from ..producer.components.queue.service import QueueService
from ..producer.components.queue.containers import QueueContainer
from ..producer.components.validator.service import ValidatorService
from ..producer.components.validator.containers import ValidatorContainer


@pytest.fixture
def container() -> ApplicationContainer:
    """Application Container overrides"""

    logger_container = LoggerContainer()
    serializer_container = SerializerContainer()

    # Need to provide a mock client for SQS
    queue_container = QueueContainer(
        config={'queue_url': 'QUEUE_URL'},
        logger=logger_container.logger
    )
    sqs_client_mock = mock.Mock()
    queue_container.sqs_client.override(sqs_client_mock)

    # Need to provide a mock client for SecretsManager
    secretsmanager_container = SecretsManagerContainer(
        config={'secret_name': 'SECRET_NAME'},
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
    )
    secretsmanager_client_mock = mock.Mock()
    # Need to provide mock value because creating a ValidatorContainer
    # depends on these values to be provided asynchronously
    secretsmanager_client_mock.get_secret_value.return_value = {
        'SecretString': '{\"SENTRY_CLIENT_SECRET\": \"Some Private Key\", \"DATADOG_SECRET_TOKEN\": \"MySuperSecretString\" }'
    }
    secretsmanager_container.secretsmanager_client.override(
        secretsmanager_client_mock)

    validator_container = ValidatorContainer(
        logger=logger_container.logger,
        development=False,
        keys=secretsmanager_container.keys
    )

    container = ApplicationContainer()
    container.validator_container.override(validator_container)
    container.queue_container.override(queue_container)
    container.secretsmanager_container.override(secretsmanager_container)
    container.serializer_container.override(serializer_container)
    container.logger_container.override(logger_container)
    return container


@pytest.mark.asyncio
async def test_application_instance(container: ApplicationContainer) -> None:
    """Test producer application instances"""
    logger_service = container.logger_container.logger_service()
    queue_service = container.queue_container.queue_service()
    secretsmanager_service = container.secretsmanager_container.secretsmanager_service()
    serializer_service = container.serializer_container.serializer_service()
    # Must await on the validator because it depends on an async initialization
    # from the secretsmanager service
    validator_service = await container.validator_container.validator_service()
    assert isinstance(logger_service, LoggerService)
    assert isinstance(queue_service, QueueService)
    assert isinstance(secretsmanager_service, SecretsManagerService)
    assert isinstance(serializer_service, SerializerService)
    assert isinstance(validator_service, ValidatorService)

    # Test that our services are singletons
    logger_service2 = container.logger_container.logger_service()
    queue_service2 = container.queue_container.queue_service()
    secretsmanager_service2 = container.secretsmanager_container.secretsmanager_service()
    serializer_service2 = container.serializer_container.serializer_service()
    # Must await on the validator because it depends on an async initialization
    # from the secretsmanager service
    validator_service2 = await container.validator_container.validator_service()
    assert logger_service == logger_service2
    assert queue_service == queue_service2
    assert secretsmanager_service == secretsmanager_service2
    assert serializer_service == serializer_service2
    assert validator_service == validator_service2
