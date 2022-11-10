# Linked to https://app.airplane.dev/t/deployment_statisitics [do not edit this line]
from datetime import datetime, timedelta

from pyshared.airplane_utils import AirplaneTask
from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.aws_secrets import get_secret_value
from pyshared.datadog.metric import DatadogMetric, Metric


class DeploymentStatistics(AirplaneTask):

    @staticmethod
    def statistics(ro_arn, state_machine_arn, date):
        client = get_credentialed_client(service_name="stepfunctions",
                                         arns=get_aws_const(ro_arn),
                                         desc="deployment_statistics",
                                         region="us-west-2")

        paginator = client.get_paginator('list_executions')
        arn = get_aws_const(state_machine_arn)

        iterator = paginator.paginate(
            stateMachineArn=arn,
            #    statusFilter='RUNNING'|'SUCCEEDED'|'FAILED'|'TIMED_OUT'|'ABORTED',
            PaginationConfig={
                'PageSize': 100,
            })
        search = f"executions[?to_string(startDate)>='\"{date}\"'][]"
        filtered = iterator.search(search)

        total = 0
        failed = 0

        for page in filtered:
            total = total + 1
            if page['status'] == 'FAILED':
                failed = failed + 1

        success = total - failed

        return {
            "total": total,
            "failed": failed,
            "success": success,
            "human_rate": f"{round(success / total * 100, 4)}%"
        }

    @staticmethod
    def get_metric(level, field, value):
        return {
            "name": f"panther.DeploymentStatistics.{level}.{field}",
            "type": "gauge",
            "points": [{"timestamp": int(datetime.now().timestamp()), "value": value}],
        }

    def update_datadog(self, report):
        datadog = DatadogMetric(api_key=get_secret_value("airplane/datadog-api-key"))

        for level in report.keys():
            for field in report[level].keys():
                if field != "human_rate":
                    value = report[level][field]
                    metric = self.get_metric(level, field, value)
                    datadog.submit(Metric(**metric))

    def main(self, params):
        print("parameters:", params)
        time_range = params["range"]
        date = self.get_date(time_range)
        print(f"Filtering from {date}")

        hosted = self.statistics("STEP_FUNCTION_HOSTED_RO_ROLE_ARN",
                                 "STATE_MACHINE_HOSTED_ARN", date)
        internal = self.statistics("STEP_FUNCTION_INTERNAL_RO_ROLE_ARN",
                                   "STATE_MACHINE_INTERNAL_ARN", date)

        total_count = hosted["total"] + internal["total"]
        total_failed = hosted["failed"] + internal["failed"]
        total_success = hosted["success"] + internal["success"]
        total_human = f"{round(total_success / total_count * 100, 4)}%"

        report = {
            "hosted": hosted,
            "internal": internal,
            "total": {
                "total": total_count,
                "failed": total_failed,
                "success": total_success,
                "human_rate": total_human,
            }
        }

        self.update_datadog(report)

        return report

    @staticmethod
    def get_date(time_range):
        options = {
            "week": datetime.today() - timedelta(weeks=1),
            "month": datetime.today().replace(day=1),
        }
        return options.get(time_range)


def main(params):
    return DeploymentStatistics().main(params)
