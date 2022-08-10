# pylint: disable=redefined-outer-name

from logging import Logger
from logging import DEBUG, INFO
import pytest
from ..common.components.logger.containers import LoggerContainer


@pytest.fixture
def container() -> LoggerContainer:
    """Logger Container overrides"""
    container = LoggerContainer(
        config={
            'common': {'is_lambda': 'true', 'development': 'false', 'debug': 'false'},
            'logging': {'root': {'level': 'DEBUG', 'handlers': ['console']}},
        },
    )
    return container


@pytest.mark.asyncio
async def test_logger_get(container: LoggerContainer) -> None:
    """Test getting a logger handle"""

    # Services are singletons
    service = container.logger_service()
    service2 = container.logger_service()
    assert service == service2

    # The service also returns a singleton handle to a Logger
    log = service.get()
    log2 = service.get()
    assert log == log2

    assert isinstance(log, Logger)


@pytest.mark.asyncio
async def test_configure_logger(container: LoggerContainer) -> None:
    """Test configuring a logger"""

    # Test with is_lambda true (default config)
    container.configure_logger()
    service = container.logger_service()
    log = service.get()
    assert log.level == INFO

    # Test local logger (with config override)
    with container.config.override(
        {
            'common': {'is_lambda': 'false', 'development': 'false', 'debug': 'false'},
            'logging': {
                'version': 1,
                'formatters': {
                    'console': {
                        'class': 'logging.Formatter',
                        'format': '[%(levelname)s] [%(asctime)s.%(msecs)03dZ] [%(pathname)s:%(funcName)s:%(lineno)d] %(message)s',
                    }
                },
                'handlers': {
                    'console': {
                        'class': 'logging.StreamHandler',
                        'level': 'INFO',
                        'formatter': 'console',
                        'stream': 'ext://sys.stdout',
                    }
                },
                'root': {'level': 'DEBUG', 'handlers': ['console']},
            },
        }
    ):
        container.configure_logger()
        service = container.logger_service()
        log = service.get()
    assert log.level == DEBUG
