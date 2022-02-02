# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import Callable, Dict


class SerializerService:
    """Serializer Service"""

    def __init__(self, serialize: Callable, deserialize: Callable):
        self.serialize = serialize
        self.deserialize = deserialize

    def stringify(self, payload: Dict) -> str:
        """Convert a dict to a str"""
        return self.serialize(payload)

    def parse(self, payload: str) -> Dict:
        """Convert a str to a dict"""
        return self.deserialize(payload)
