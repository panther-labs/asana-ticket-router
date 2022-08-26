# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=too-many-arguments
from typing import Dict
from logging import Logger
from common.constants import DATADOG_SOURCE_TYPE
from common.components.serializer.service import SerializerService
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.events_api import EventsApi
from datadog_api_client.v1.model.event_create_request import EventCreateRequest


class DatadogService:
    """Datadog Service"""

    def __init__(
        self,
        logger: Logger,
        serializer: SerializerService,
        client: ApiClient,
        datadog_api_key: str,
        datadog_app_key: str,
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

    async def post_event_details(self, datadog_event: Dict) -> Dict:
        """Post an event to the datadog event stream."""
        api_instance = EventsApi(self._client)
        req = EventCreateRequest(**datadog_event)
        response = api_instance.create_event(body=req)
        return response.to_dict()


def make_datadog_asana_event(record: Dict, asana_link: str) -> dict:
    """Convert a datadog event into an asana event so we can look it up later."""
    # Careful, we don't want to modify record['tags'], just copy it.
    tags = record.get('tags', []).copy()
    alert_title = record.get('title', '')
    monitor_id = record.get('monitor_id', 'missing')
    tags.extend([f'monitor_id:{monitor_id}', 'event_source:asana'])
    return {
        'title': f'Created Asana task for {alert_title}',
        'text': asana_link,
        'source_type_name': DATADOG_SOURCE_TYPE,
        'tags': tags,
    }
