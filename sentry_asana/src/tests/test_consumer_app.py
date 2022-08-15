# pylint: disable=redefined-outer-name
import pytest
from unittest import mock

from ..common.components.secrets.service import SecretsManagerService
from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.serializer.service import SerializerService
from ..common.components.serializer.containers import SerializerContainer
from ..common.components.logger.service import LoggerService
from ..common.components.logger.containers import LoggerContainer
from ..common.components.entities.containers import EntitiesContainer
from ..common.components.entities.service import TeamService
from ..consumer.components.application import ApplicationContainer
from ..consumer.components.sentry.containers import SentryContainer
from ..consumer.components.requests.containers import RequestsContainer
from ..consumer.components.sentry.service import SentryService
from ..consumer.components.asana.containers import AsanaContainer
from ..consumer.components.asana.service import AsanaService
from ..consumer.components.datadog.service import DatadogService
from . import test_entities


@pytest.fixture
def container() -> ApplicationContainer:
    """Application Container overrides"""

    logger_container = LoggerContainer()
    serializer_container = SerializerContainer()
    requests_container = RequestsContainer()
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
        'SecretString': '{\"SENTRY_CLIENT_SECRET\": \"Some Private Key\",'
        '\"ASANA_PAT\": \"Some PAT\",'
        '\"SENTRY_PAT\": \"Some PAT\",'
        '\"DATADOG_API_KEY\": \"MyDatadogAPIKey\", '
        '\"DATADOG_APP_KEY\": \"MyDatadogAppKey\"}'
    }
    secretsmanager_container.secretsmanager_client.override(secretsmanager_client_mock)

    entity_contianer = EntitiesContainer(
        config={'entities': {'team_data_file': test_entities.team_data_file()}}
    )

    sentry_container = SentryContainer(
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        requests=requests_container,
        keys=secretsmanager_container.keys,
    )

    asana_container = AsanaContainer(
        config={
            'development': 'false',
            'dev_asana_sentry_project': '123',
            'release_testing_portfolio': '123',
        },
        logger=logger_container.logger,
        serializer=serializer_container.serializer_service,
        keys=secretsmanager_container.keys,
    )

    container = ApplicationContainer()
    container.secretsmanager_container.override(secretsmanager_container)
    container.serializer_container.override(serializer_container)
    container.logger_container.override(logger_container)
    container.sentry_container.override(sentry_container)
    container.asana_container.override(asana_container)
    container.entities_container.override(entity_contianer)
    return container


@pytest.mark.asyncio
async def test_application_instance(container: ApplicationContainer) -> None:
    """Test consumer application instances"""
    logger_service = container.logger_container.logger_service()
    secretsmanager_service = container.secretsmanager_container.secretsmanager_service()
    serializer_service = container.serializer_container.serializer_service()
    teams_service = container.entities_container.teams_service()
    # Must await on the sentry and asana services because they depend
    # on an async initialization from the secretsmanager service
    sentry_service = await container.sentry_container.sentry_service()
    asana_service = await container.asana_container.asana_service()
    datadog_service = await container.datadog_container.datadog_service()
    assert isinstance(logger_service, LoggerService)
    assert isinstance(secretsmanager_service, SecretsManagerService)
    assert isinstance(serializer_service, SerializerService)
    assert isinstance(sentry_service, SentryService)
    assert isinstance(asana_service, AsanaService)
    assert isinstance(datadog_service, DatadogService)
    assert isinstance(teams_service, TeamService)

    # Test that our services are singletons
    logger_service2 = container.logger_container.logger_service()
    secretsmanager_service2 = (
        container.secretsmanager_container.secretsmanager_service()
    )
    serializer_service2 = container.serializer_container.serializer_service()
    teams_service2 = container.entities_container.teams_service()
    # Must await on the sentry and asana services because they depend
    # on an async initialization from the secretsmanager service
    sentry_service2 = await container.sentry_container.sentry_service()
    asana_service2 = await container.asana_container.asana_service()
    datadog_service2 = await container.datadog_container.datadog_service()
    assert logger_service == logger_service2
    assert secretsmanager_service == secretsmanager_service2
    assert serializer_service == serializer_service2
    assert sentry_service == sentry_service2
    assert asana_service == asana_service2
    assert datadog_service == datadog_service2
    assert teams_service == teams_service2
