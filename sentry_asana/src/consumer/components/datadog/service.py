# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=too-many-arguments
from typing import Dict
from logging import Logger
from common.components.serializer.service import SerializerService
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.events_api import EventsApi


class DatadogService:
    """Datadog Service"""

    def __init__(
        self,
        logger: Logger,
        serializer: SerializerService,
        client: ApiClient,
        datadog_api_key: str,
        datadog_app_key: str

    ):
        self._logger = logger
        self._serializer = serializer
        self._client = client

        configuration = Configuration()
        configuration.api_key['apiKeyAuth'] = datadog_api_key
        configuration.api_key['appKeyAuth'] = datadog_app_key

        self._client.configuration = configuration

    async def get_event_details(self, datadog_event: Dict) -> Dict:
        """Get Event Details about a Datadog Alarm Event"""
        api_instance = EventsApi(self._client)
        response = api_instance.get_event(event_id=int(datadog_event['id']))
        return response.to_dict()
