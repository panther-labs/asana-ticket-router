import asyncio
import pytest
from unittest import mock

from ..common.components.secrets.service import SecretsManagerService
from ..common.components.secrets.containers import SecretsManagerContainer
from ..common.components.serializer.service import SerializerService
from ..common.components.serializer.containers import SerializerContainer
from ..common.components.logger.service import LoggerService
from ..common.components.logger.containers import LoggerContainer
from ..consumer.components.application import ApplicationContainer
from ..consumer.components.sentry.containers import SentryContainer
from ..consumer.components.requests.containers import RequestsContainer
from ..consumer.components.sentry.service import SentryService
from ..consumer.components.asana.containers import AsanaContainer
from ..consumer.components.asana.service import AsanaService

from ..common.components.entities.service import TeamService
from ..common.components.entities.containers import EntitiesContainer


@pytest.fixture
def container_with_mock() -> EntitiesContainer:
  return EntitiesContainer(logger=LoggerContainer().logger)

def test_TeamsServiceInit(container_with_mock: EntitiesContainer) -> None:
  teams_service = container_with_mock.teams_service()
  assert teams_service.DefaultService() != []