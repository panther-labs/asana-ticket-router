# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=too-many-arguments
from typing import Dict
from logging import Logger
from urllib import parse
from datetime import datetime, timezone
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.events_api import EventsApi
from datadog_api_client.v1.model.event_create_request import EventCreateRequest
from common.constants import DATADOG_SOURCE_TYPE
from common.components.serializer.service import SerializerService
from common.components.entities.service import EngTeam
from consumer.components.asana.entities import AsanaFields, PRIORITY, RUNBOOK_URL


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


def extract_datadog_fields(
    datadog_event: Dict, team: EngTeam, routing_data: str
) -> AsanaFields:
    """Extract relevent fields from the datadog event"""
    url = datadog_event['link']
    tag_list = datadog_event['tags'].split(',')
    tags = tag_list_to_dict(tag_list)
    aws_region = tags.get('region', 'Unknown')
    aws_account_id = tags.get('aws_account', 'Unknown')
    customer = tags.get('customer_name', 'Unknown')
    display_name = parse.quote(customer)
    event_datetime = datetime.fromtimestamp(
        int(datadog_event['date']) / 1000, tz=timezone.utc
    ).strftime('%Y-%m-%dT%H:%M:%SZ')
    title = datadog_event["title"]
    if customer != 'Unknown':
        title = f'{title} | Customer: {customer}'
    datadog_priority = datadog_event.get('priority', 'Unknown').lower()
    priority = get_datadog_task_priority(datadog_priority)
    environment = tags.get('env', 'Unknown').lower()
    runbook_url = RUNBOOK_URL
    return AsanaFields(
        assigned_team=team,
        aws_account_id=aws_account_id,
        aws_region=aws_region,
        customer=customer,
        display_name=display_name,
        environment=environment,
        event_datetime=event_datetime,
        priority=priority,
        runbook_url=runbook_url,
        tags=tags,
        title=title,
        url=url,
        routing_data=routing_data,
    )


def tag_list_to_dict(tag_list: list) -> dict:
    """Converts a list of colon delimited Key/Value pairs to a dictionary."""

    tags = {}
    for tag in tag_list:
        key: str = tag
        value: str = ''

        if ':' in tag:
            key = tag.split(':')[0]
            value = tag.split(':')[1]

        tags[key] = value

    return tags


def get_datadog_task_priority(level: str) -> PRIORITY:
    """Returns a PRIORITY Enum based on the Datadog event level provided."""

    if level in ['p5', 'p4', 'p3']:
        return PRIORITY.MEDIUM

    return PRIORITY.HIGH
