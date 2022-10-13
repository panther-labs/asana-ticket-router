from dataclasses import dataclass

from datadog_api_client.v2.api.metrics_api import MetricsApi
from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
from datadog_api_client.v2.model.metric_payload import MetricPayload
from datadog_api_client.v2.model.metric_point import MetricPoint
from datadog_api_client.v2.model.metric_series import MetricSeries

from . import Datadog


@dataclass
class Metric:
    name: str
    type: str
    points: list
    tags: list = None

class DatadogMetric(Datadog):
    def __init__(self, api_key):
        super().__init__(api_key=api_key)
        self.api = MetricsApi(self.client)

    def submit(self, metric: Metric):
        metric_points = []
        for point in metric.points:
            metric_point = MetricPoint(timestamp=point["timestamp"], value=point["value"])
            metric_points.append(metric_point)

        body = MetricPayload(
            series=[
                MetricSeries(
                    metric=metric.name,
                    type=MetricIntakeType(self._metric_intake_type(metric.type)),
                    points=metric_points,
                    tags=metric.tags
                ),
            ],
        )

        return self.api.submit_metrics(body=body)

    def _metric_intake_type(self, metric_type):
        metric_types = {
            "unspecified": 0,
            "count": 1,
            "rate": 2,
            "gauge": 3
        }

        return metric_types[metric_type]
