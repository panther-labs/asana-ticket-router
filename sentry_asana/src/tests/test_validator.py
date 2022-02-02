# pylint: disable=redefined-outer-name

import pytest
from ..producer.components.validator.containers import ValidatorContainer
from ..producer.components.logger.containers import LoggerContainer


@pytest.fixture
def container() -> ValidatorContainer:
    """Secrets Container overrides"""
    container = ValidatorContainer(
        logger=LoggerContainer.logger,
        development=False
    )
    return container


@pytest.mark.asyncio
async def test_hash(container: ValidatorContainer) -> None:
    """Test getting a secret"""

    service = container.validator_service()
    hashed = await service.hash('Hello World', 'Some Private Key')
    assert hashed == '64634bbddfd3a1bb0d6360839371aa12ea16d785c7f94bb6f2eac7ed5f3d235c'  # hmac-sha256


@pytest.mark.asyncio
async def test_validate(container: ValidatorContainer) -> None:
    """Test getting a secret"""

    service = container.validator_service()
    signature = '64634bbddfd3a1bb0d6360839371aa12ea16d785c7f94bb6f2eac7ed5f3d235c'  # hmac-sha256
    is_valid = await service.validate('Hello World', signature, 'Some Private Key')
    assert is_valid is True

    # When in development mode, test that we bypass the signature check
    with container.development.override(True):
        # Reset our singleton and create a new one that takes the override
        container.validator_service.reset()
        service = container.validator_service()
        is_valid = await service.validate('Hello World', 'Bad Signature', 'Some Private Key')
    assert is_valid is True
