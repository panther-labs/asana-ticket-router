# Linked to https://app.airplane.dev/t/wait_for_step_function_completion [do not edit this line]
import datetime
import pprint
import os
import tenacity

from pyshared.aws_creds import get_credentialed_client

STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")
STATE_MACHINE_POLL_FREQUENCY_SECS = 60
STATE_MACHINE_TIMEOUT_SECS = 3600
STEP_FUNCTION_RO_ROLE_ARN = os.environ.get("STEP_FUNCTION_RO_ROLE_ARN")
STEP_FUNCTION_REGION = os.environ.get("STEP_FUNCTION_REGION")


def print_after_query(retry_state):
    print(f"{datetime.datetime.now()}: State machine still has 'RUNNING' status...")


def raise_exception_after_query_fails(retry_state):
    raise RuntimeError("Timed out waiting for state machine to finish. It is still running...")


@tenacity.retry(after=print_after_query,
                retry=tenacity.retry_if_result(lambda account_execution: account_execution["status"] == "RUNNING"),
                retry_error_callback=raise_exception_after_query_fails,
                stop=tenacity.stop_after_delay(STATE_MACHINE_TIMEOUT_SECS),
                wait=tenacity.wait_fixed(STATE_MACHINE_POLL_FREQUENCY_SECS))
def wait_until_state_machine_finished(client, execution_arn):
    return client.describe_execution(executionArn=execution_arn)


def get_execution_arn(client, fairytale_name):
    paginator = client.get_paginator('list_executions')
    page_iterator = paginator.paginate(stateMachineArn=STATE_MACHINE_ARN)
    search = f"executions[?contains(name, '{fairytale_name}')]"
    fairytale_execution = next((execution for execution in page_iterator.search(search)), None)
    if fairytale_execution is None:
        raise ValueError(f"Could not find state machine execution for fairytale_name {fairytale_name}")

    return fairytale_execution["executionArn"]


def main(params):
    client = get_credentialed_client(service_name="stepfunctions",
                                     arns=STEP_FUNCTION_RO_ROLE_ARN,
                                     desc="wait_for_step_function_completion",
                                     region=STEP_FUNCTION_REGION)

    fairytale_execution = wait_until_state_machine_finished(client=client,
                                                            execution_arn=get_execution_arn(
                                                                client, params["fairytale_name"]))

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
