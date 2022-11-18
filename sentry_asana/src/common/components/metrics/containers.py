# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors

from datadog_lambda import metric as dd_metrics
from dependency_injector import containers, providers
from . import service


class MetricsContainer(containers.DeclarativeContainer):
    """Metrics Container"""

    config = providers.Configuration(strict=True)
    metrics = providers.Dependency(default=dd_metrics.lambda_metric)
    metrics_client = providers.Singleton(metrics)
    metrics_service = providers.Singleton(service.MetricsService, client=metrics_client)
    metrics_sink = providers.Singleton(
        service.MetricSink, metrics_service=metrics_service
    )
