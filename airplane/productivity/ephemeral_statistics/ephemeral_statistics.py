from datetime import datetime, timedelta
import base64
import dateutil
import json

from pyshared.airplane_utils import AirplaneTask
from pyshared.aws_creds import get_credentialed_client


class EphemeralStatistics(AirplaneTask):
    IN_USE = 1
    MAX_CLEANUP_ATTEMPTS = 5
    CLEANUP_FAILED_RESULT = "failed"

    def __init__(self):
        super().__init__()
        self.client = get_credentialed_client(service_name="lambda",
                                              arns="arn:aws:iam::292442345278:role/EphemeralDeploymentAdmin",
                                              region="us-west-2",
                                              desc="airplane",
                                              test_role=self.test_roles.get("ephemeral_admin"))
        self.one_day_ago = datetime.today() - timedelta(days=1)
        self.one_week_ago = datetime.today() - timedelta(weeks=1)

    def main(self, params):
        deployment_info = self._get_deployment_info()

        return {
            "hosts": {
                "count":
                self.count("SELECT count(*) FROM hosts"),
                "in_use":
                self.count(f"SELECT count(*) FROM hosts where state = {self.IN_USE}"),
                "in_cleanup":
                self.count("SELECT count(*) FROM hosts inner join ref_hosts "
                           "ON ref_hosts.id = hosts.ref_host_id WHERE "
                           "teardown_build_id is not null and "
                           f"teardown_count != {self.MAX_CLEANUP_ATTEMPTS} and "
                           f"teardown_build_result != '{self.CLEANUP_FAILED_RESULT}'"),
                "failed_teardown":
                self.count(f"SELECT count(*) FROM hosts inner join ref_hosts "
                           "ON ref_hosts.id = hosts.ref_host_id WHERE "
                           "teardown_build_id is not null and "
                           f"teardown_count = {self.MAX_CLEANUP_ATTEMPTS} and "
                           f"teardown_build_result = '{self.CLEANUP_FAILED_RESULT}'"),
            },
            "prs": {
                "open": self.count("SELECT count(*) FROM refs where github_state = 1"),
            },
            "deployments_past_day": deployment_info["one_day"],
            "deployments_past_week": deployment_info["one_week"],
            "average_deploy_time": {
                "daily": self._get_avg_deploy_times(start_time=self.one_day_ago),
                "weekly": self._get_avg_deploy_times(start_time=self.one_week_ago)
            }
        }

    def count(self, query):
        output = self.invoke(query)
        if not output:
            return 0
        return output[0].get("count", 0)

    def invoke(self, query):
        print(query) # Useful for debugging execution failures

        message_bytes = query.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes).decode("utf-8")
        payload = {'sql': {'query': base64_bytes}}

        response = self.client.invoke(
            FunctionName="ephemeral-deployments-admin-host",
            Payload=json.dumps(payload),
            InvocationType="RequestResponse",
        )

        res = response.get('Payload').read().decode()
        res_json = json.loads(res)

        if 'FunctionError' in response:
            raise Exception(f"\n\tQuery: {query}\n\tResponse: {res_json}")

        output = res_json.get("sql", {}).get("result", {})
        return output

    def _get_deployment_info(self):
        deployment_info = {}

        for range_name, datetime_obj in (("one_day", self.one_day_ago), ("one_week", self.one_week_ago)):
            deployment_info[range_name] = {
                "count":
                self.count(f"SELECT count(*) FROM deployments where created_at > '{datetime_obj}'"),
                "success":
                self.count(f"SELECT count(*) FROM deployments where step_function_result = 'success'"
                           f" and created_at > '{datetime_obj}'"),
                "failed":
                self.count(f"SELECT count(*) FROM deployments where step_function_result = 'failed'"
                           f" and created_at > '{datetime_obj}'"),
                "failed_pulumi":
                self.count(f"SELECT count(*) FROM deployments where step_function_result = 'failed'"
                           f" and failure_reason like 'Pulumi Failure%'"
                           f" and created_at > '{datetime_obj}'"),
                "failed_cloudformation":
                self.count(f"SELECT count(*) FROM deployments where step_function_result = 'failed'"
                           f" and failure_reason like 'Cloudformation failure%'"
                           f" and created_at > '{datetime_obj}'"),
                "timeout":
                self.count(f"SELECT count(*) FROM deployments where step_function_result = 'timeout'"
                           f" and created_at > '{datetime_obj}'"),
                "in_progress":
                self.count(f"SELECT count(*) FROM deployments where step_function_result is null"
                           f" and created_at > '{datetime_obj}'")
            }

        return deployment_info

    def _get_avg_from_query(self, start_time, comparison):
        deployments = self.invoke(f"SELECT rank_filter.updated_at - rank_filter.created_at as diff FROM (select deployments.*, rank() over (partition by ref_host_id order by created_at) from deployments) rank_filter where step_function_result = 'success' and {comparison} and created_at > '{start_time}'")

        result = 0
        if deployments is not None:
            total_deploys = len(deployments)
            deploy_time_sum = timedelta(seconds=0)
            for deployment_times in deployments:
                deploy_time_sum += (dateutil.parser.parse(deployment_times["diff"]) -
                                    dateutil.parser.parse('00:00:00.00'))
            result = deploy_time_sum / total_deploys
        return result

    def _get_avg_deploy_times(self, start_time):
        return {
            "initial": str(self._get_avg_from_query(start_time, "rank = 1")),
            "upgrades": str(self._get_avg_from_query(start_time, "rank != 1")),
        }

    def get_failure_slack_channel(self):
        return "#eng-ops"


def main(_):
    return EphemeralStatistics().main_notify_failures({})


if __name__ == "__main__":
    print(main({}))
