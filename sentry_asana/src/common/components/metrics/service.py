# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import Any, List
from common.constants import AlertType


class MetricsService:
    """Metrics Service"""

    def __init__(self, client: Any):
        self._client = client

    def emit_metric(
        self, metric_name: str, metric_value: float, tags: List[str]
    ) -> None:
        """EmitMetric emits a metric into the metric sink.

        EmitMetric emits "distribution" metrics because of intricacies in how our metrics provider (currently datadog)
        handles timeseries points with similar timestamps.
        """
        self._client(metric_name, metric_value, tags=tags)


class MetricSink:
    """Metrics Sink just lists our metrics and their tags."""

    # All sentry2asana metrics should this metric prefix, to segment them.
    SENTRY_ASANA_METRIC_PREFIX = 'panther.sentry2asana'

    TICKET_COUNT = f'{SENTRY_ASANA_METRIC_PREFIX}.ticket.count'
    EVENT_COUNT = f'{SENTRY_ASANA_METRIC_PREFIX}.event.count'

    def __init__(self, metrics_service: MetricsService) -> None:
        self._metrics = metrics_service

    def increment_ticket_count(self, team: str, source: AlertType) -> None:
        """increment_ticket_count increments the ticket count metric.

        ticket.count is the # of tickets we filed to Asana.
        ticket.count has two tags, the team name we routed the ticket to, and the ticket source (sentry or datadog)
        """
        self._metrics.emit_metric(
            MetricSink.TICKET_COUNT, 1.0, tags=[f'team:{team}', f'kind:{source.name}']
        )

    def increment_event_count(
        self, kind: AlertType, component: str, valid: bool
    ) -> None:
        """increment_event_count counts the number of events we observed, by type, and whether they were valid or not.

        event.count is a count of events sentry2asana received.
        event.count has 3 tags:
        component:<name> is either producer, or consumer.
        valid:<true|false> is a boolean value, true if the event was valid, false for invalid events which are ignored.
        kind: which kind of event it is, either SENTRY, ASANA, or UNKNOWN
        """
        self._metrics.emit_metric(
            MetricSink.EVENT_COUNT,
            1.0,
            tags=[
                f'kind:{str(kind.name)}',
                f'component:{component}',
                f'valid:{valid}',
            ],
        )
