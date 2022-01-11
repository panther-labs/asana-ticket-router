# Linked to https://app.airplane.dev/t/deployment_statisitics [do not edit this line]
import boto3
import os
from datetime import datetime, timedelta


def main(params):
    print("parameters:", params)
    range = params["range"]
    date = get_date(range)
    print(f"Filtering from {date}")

    root_conn = assume_hosted_root_role()
    client = get_client(root_conn, "stepfunctions", "us-west-2")

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

    return {
        "total": total,
        "failed": failed,
        "human_rate": f"{round(success / total * 100, 4)}%"
    }


def get_date(range):
    options = {
        "week": datetime.today() - timedelta(weeks=1),
        "month": datetime.today().replace(day=1),
    }
    return options.get(range)


def get_client(conn, client, region):
    return boto3.client(
        client,
        aws_access_key_id=conn["Credentials"]["AccessKeyId"],
        aws_secret_access_key=conn["Credentials"]["SecretAccessKey"],
        aws_session_token=conn["Credentials"]["SessionToken"],
        region_name=region,
    )


def assume_hosted_root_role():
    sts_conn = boto3.client("sts")

    hosted_root_arn = os.environ.get(
        "HOSTED_ROOT_ROLE_ARN",
        "arn:aws:iam::255674391660:role/AirplaneStepFunctionReadOnly")

    return sts_conn.assume_role(
        RoleArn=hosted_root_arn,
        RoleSessionName="airplane_productivity",
    )
