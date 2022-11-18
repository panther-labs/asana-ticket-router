# import pytest
import unittest.mock as mock

from common.constants import AlertType
from common.components.metrics.containers import MetricsContainer
from common.components.metrics.service import MetricSink
import datadog_lambda


def test_EmitMetric() -> None:
    container = MetricsContainer(config={})
    metrics_mock = mock.create_autospec(datadog_lambda.metric.lambda_metric)
    container.metrics_client.override(metrics_mock)
    metrics_service = container.metrics_sink()
    metrics_service.increment_event_count(AlertType.UNKNOWN_ALERT, 'testing', True)

    assert metrics_mock.called
    assert metrics_mock.call_count == 1
