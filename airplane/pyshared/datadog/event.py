""" Manage Datadog events """

import re
from dataclasses import dataclass
from datadog_api_client.v1.api.events_api import EventsApi
from datadog_api_client.v1.model.event_create_request import EventCreateRequest

from . import Datadog

@dataclass
class Event:
    title: str
    text: str
    tags: list = None

class DatadogEvent(Datadog):
    def __init__(self, api_key):
        super().__init__(api_key=api_key)
        self.api = EventsApi(self.client)

    def submit(self, event: Event):
        body = EventCreateRequest(
            title=event.title,
            text=event.text,
            tags=event.tags,
        )

        return self.api.create_event(body=body)
