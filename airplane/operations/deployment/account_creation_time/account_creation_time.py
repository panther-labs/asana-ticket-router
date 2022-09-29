from datetime import datetime

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.metrics_api import MetricsApi
from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
from datadog_api_client.v2.model.metric_payload import MetricPayload
from datadog_api_client.v2.model.metric_point import MetricPoint
from datadog_api_client.v2.model.metric_series import MetricSeries

from pyshared.aws_secrets import get_secret_value


def main(params):
  start_time = datetime.fromtimestamp(params["start_time"])
  now_time = datetime.now()
  time_diff = (now_time - start_time).total_seconds()
  datadog_api_key = get_secret_value("airplane/datadog-api-key")

  body = MetricPayload(
    series=[
      MetricSeries(
        metric="panther.PLGDeploymentTime",
        type=MetricIntakeType(3),
        points=[
          MetricPoint(
            timestamp=int(datetime.now().timestamp()),
            value=time_diff,
          ),
        ],
        tags=[f"customer_name:{params['fairytale_name']}"]
      ),
    ],
  )

  configuration = Configuration()
  configuration.api_key["apiKeyAuth"] = datadog_api_key

  with ApiClient(configuration) as api_client:
      api_instance = MetricsApi(api_client)
      response = api_instance.submit_metrics(body=body)

      print(response)

  return {'time_diff': time_diff}
