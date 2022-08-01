# Linked to https://app.airplane.dev/t/deployment_statisitics [do not edit this line]
from datetime import datetime, timedelta

from pyshared.airplane_utils import AirplaneTask
from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client


class DeploymentStatistics(AirplaneTask):
    def main(self, params):
        print("parameters:", params)
        time_range = params["range"]
        date = self.get_date(time_range)
        print(f"Filtering from {date}")

        client = get_credentialed_client(service_name="stepfunctions",
                                         arns=get_aws_const("STEP_FUNCTION_RO_ROLE_ARN"),
                                         desc="deployment_statistics",
                                         region="us-west-2")

        paginator = client.get_paginator('list_executions')
        arn = 'arn:aws:states:us-west-2:255674391660:stateMachine:AutomatedDeploymentStateMachine-y5bh5L9a5z41'

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

        return {"total": total, "failed": failed, "success": success, "human_rate": f"{round(success / total * 100, 4)}%"}

    @staticmethod
    def get_date(time_range):
        options = {
            "week": datetime.today() - timedelta(weeks=1),
            "month": datetime.today().replace(day=1),
        }
        return options.get(time_range)

    def get_failure_slack_channel(self):
        return "#triage-deployment"


def main(params):
    return DeploymentStatistics().main_notify_failures(params)
