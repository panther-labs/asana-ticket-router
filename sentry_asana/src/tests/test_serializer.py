# pylint: disable=redefined-outer-name

import pytest
from ..producer.components.serializer.containers import SerializerContainer


@pytest.fixture
def container() -> SerializerContainer:
    """Serializer Container overrides"""
    return SerializerContainer()


@pytest.mark.asyncio
async def test_serialize(container: SerializerContainer) -> None:
    """Test serialization"""

    service = container.serializer_service()

    serialized = service.stringify({'Key': 'Value'})
    assert serialized == "{\"Key\": \"Value\"}"


@pytest.mark.asyncio
async def test_deserialize(container: SerializerContainer) -> None:
    """Test serialization"""

    service = container.serializer_service()

    deserialized = service.parse("{\"Key\": \"Value\"}")
    assert deserialized == {'Key': 'Value'}
