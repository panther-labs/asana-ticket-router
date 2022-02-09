# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import Any, Dict


class SerializerService:
    """Serializer Service"""

    def __init__(self, client: Any):
        self._client = client

    def stringify(self, payload: Dict) -> str:
        """Convert a dict to a str"""
        return self._client.dumps(payload)

    def parse(self, payload: str) -> Dict:
        """Convert a str to a dict"""
        return self._client.loads(payload)
