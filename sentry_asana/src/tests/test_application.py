# pylint: disable=redefined-outer-name
import os
import pytest
from unittest import mock
from ..producer.components.application import ApplicationContainer
from ..producer.components.queue.service import QueueService
from ..producer.components.queue.containers import QueueContainer
from ..producer.components.secrets.service import SecretsManagerService
from ..producer.components.secrets.containers import SecretsManagerContainer
from ..producer.components.serializer.service import SerializerService
from ..producer.components.serializer.containers import SerializerContainer
from ..producer.components.validator.service import ValidatorService
from ..producer.components.validator.containers import ValidatorContainer
from ..producer.components.logger.service import LoggerService
from ..producer.components.logger.containers import LoggerContainer

# Set environment vars for the configs that are loaded at runtime
os.environ['SECRET_NAME'] = 'SECRET_NAME'
os.environ['QUEUE_URL'] = 'QUEUE_URL'
os.environ['IS_LAMBDA'] = 'false'
os.environ['DEBUG'] = 'false'
os.environ['DEVELOPMENT'] = 'false'


@pytest.fixture
def container() -> ApplicationContainer:
    """Application Container overrides"""

    logger_container = LoggerContainer()
    logger_container.config.from_yaml(
        'producer/config.yml',
        required=True,
        envs_required=True
    )
    serializer_container = SerializerContainer()
    validator_container = ValidatorContainer(
        logger=logger_container.logger,
        development=False
    )

    # Need to provide a mock client for SQS so it
    # doesn't complain about boto3 region not set.
    queue_container = QueueContainer(
        config={"queue_url": os.environ['QUEUE_URL']},
        logger=logger_container.logger
    )
    sqs_client_mock = mock.Mock()
    queue_container.sqs_client.override(sqs_client_mock)

    # Need to provide a mock client for SecretsManager so it
    # doesn't complain about boto3 region not set.
    secretsmanager_container = SecretsManagerContainer(
        config={"secret_name": os.environ['SECRET_NAME']},
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service(),
    )
    secretsmanager_client_mock = mock.Mock()
    secretsmanager_container.secretsmanager_client.override(
        secretsmanager_client_mock)

    container = ApplicationContainer()
    container.config.from_yaml(
        'producer/config.yml',
        required=True,
        envs_required=True
    )
    container.validator_container.override(validator_container)
    container.queue_container.override(queue_container)
    container.secretsmanager_container.override(secretsmanager_container)
    container.serializer_container.override(serializer_container)
    container.logger_container.override(logger_container)
    return container


@pytest.mark.asyncio
async def test_application_instance(container: ApplicationContainer) -> None:
    """Test application instances"""
    logger_service = container.logger_container.logger_service()
    queue_service = container.queue_container.queue_service()
    secretsmanager_service = container.secretsmanager_container.secretsmanager_service()
    serializer_service = container.serializer_container.serializer_service()
    validator_service = container.validator_container.validator_service()
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
    validator_service2 = container.validator_container.validator_service()
    assert logger_service == logger_service2
    assert queue_service == queue_service2
    assert secretsmanager_service == secretsmanager_service2
    assert serializer_service == serializer_service2
    assert validator_service == validator_service2
