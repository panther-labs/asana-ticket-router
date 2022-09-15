# Linked to https://app.airplane.dev/t/wait_for_step_function_completion [do not edit this line]
import datetime
import pprint

from botocore import exceptions
import tenacity

from pyshared.airplane_utils import AirplaneTask
from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client

STATE_MACHINE_ARN = get_aws_const(const_name="STATE_MACHINE_HOSTED_ARN")
STATE_MACHINE_POLL_FREQUENCY_SECS = 60
STATE_MACHINE_TIMEOUT_SECS = 7200
STEP_FUNCTION_RO_ROLE_ARN = get_aws_const(const_name="STEP_FUNCTION_HOSTED_RO_ROLE_ARN")
STEP_FUNCTION_REGION = get_aws_const(const_name="STEP_FUNCTION_RO_ROLE_REGION")


def print_after_query(retry_state):
    print(f"{datetime.datetime.now()}: State machine still has 'RUNNING' status...")


def raise_exception_after_query_fails(retry_state):
    raise RuntimeError("Timed out waiting for state machine to finish. It is still running...")


class StepFunctionPoller(AirplaneTask):

    def __init__(self):
        super().__init__()
        self.client = self._get_client()
        self.execution_arn = None

    @tenacity.retry(after=print_after_query,
                    retry=tenacity.retry_if_result(lambda account_execution: account_execution["status"] == "RUNNING"),
                    retry_error_callback=raise_exception_after_query_fails,
                    stop=tenacity.stop_after_delay(STATE_MACHINE_TIMEOUT_SECS),
                    wait=tenacity.wait_fixed(STATE_MACHINE_POLL_FREQUENCY_SECS))
    def wait_until_state_machine_finished(self):
        try:
            return self.client.describe_execution(executionArn=self.execution_arn)
        except exceptions.ClientError:
            print("Refreshing the boto3 client")
            self.client = self._get_client()
            return self.client.describe_execution(executionArn=self.execution_arn)

    def get_execution_arn(self, fairytale_name):
        paginator = self.client.get_paginator('list_executions')
        page_iterator = paginator.paginate(stateMachineArn=STATE_MACHINE_ARN)
        search = f"executions[?contains(name, '{fairytale_name}')]"
        fairytale_execution = next((execution for execution in page_iterator.search(search)), None)
        if fairytale_execution is None:
            raise ValueError(f"Could not find state machine execution for fairytale_name {fairytale_name}")

        return fairytale_execution["executionArn"]

    @staticmethod
    def _get_client():
        return get_credentialed_client(service_name="stepfunctions",
                                       arns=STEP_FUNCTION_RO_ROLE_ARN,
                                       desc="wait_for_step_function_completion",
                                       region=STEP_FUNCTION_REGION)

    def main(self, params):
        self.execution_arn = self.get_execution_arn(params["fairytale_name"])
        fairytale_execution = self.wait_until_state_machine_finished()

        if fairytale_execution["status"] != "SUCCEEDED":
            raise RuntimeError(f"State machine failed! {fairytale_execution}")

        return_val = {
            "executionArn": fairytale_execution["executionArn"],
            "stateMachineArn": fairytale_execution["stateMachineArn"],
            "status": fairytale_execution["status"],
            "startDate": str(fairytale_execution["startDate"]),
            "stopDate": str(fairytale_execution["stopDate"])
        }
        pprint.pprint(return_val)

        return return_val


def main(params):
    StepFunctionPoller().main(params)
