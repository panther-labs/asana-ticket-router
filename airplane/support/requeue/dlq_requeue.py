# Linked to https://app.airplane.dev/t/dlq_requeue [do not edit this line]

import boto3
import os
import json


def main(params):
    account = params["aws_account_id"]
    from_queue = params["from_queue"]
    to_queue = params["to_queue"]
    region = params["region"]

    # Auditing - AIRPLANE_RUNNER_EMAIL

    # Assume role in hosted-root
    hosted_root_conn = assume_hosted_root_support_role()
    hosted_root_sts_client = get_client(hosted_root_conn, "sts", region)

    # Assume role in saas account
    customer_acc_conn = assume_customer_support_role(hosted_root_sts_client,
                                                     account, region)

    # Invoke ops-tool
    lambda_client = get_client(customer_acc_conn, "lambda", region)
    invoke(lambda_client, from_queue, to_queue)


def assume_hosted_root_support_role():
    sts_conn = boto3.client("sts")

    hosted_root_arn = os.environ.get(
        "HOSTED_ROOT_SUPPORT_ROLE_ARN",
        "arn:aws:iam::255674391660:role/AirplaneCustomerSupport")

    return sts_conn.assume_role(
        RoleArn=hosted_root_arn,
        RoleSessionName="airplane_support",
    )


def assume_customer_support_role(conn, account_id, region):
    role_name = f"PantherSupportRole-{region}"

    customer_role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    print("customer_role_arn: ", customer_role_arn)

    return conn.assume_role(
        RoleArn=customer_role_arn,
        RoleSessionName="airplane_support",
    )


def invoke(client, from_queue, to_queue):
    payload = {'requeue': {'toQueue': from_queue, 'fromQueue': to_queue}}

    print("payload: ", payload)

    response = client.invoke(
        FunctionName="panther-ops-tools",
        Payload=json.dumps(payload),
        InvocationType="RequestResponse",
    )

    print(response.get('Payload').read().decode())


def get_client(conn, client, region):
    return boto3.client(
        client,
        aws_access_key_id=conn["Credentials"]["AccessKeyId"],
        aws_secret_access_key=conn["Credentials"]["SecretAccessKey"],
        aws_session_token=conn["Credentials"]["SessionToken"],
        region_name=region,
    )


if __name__ == "__main__":
    params = {
        # papaya-oarfish
        'aws_account_id': "548688929292",
        'from_queue': "panther-alerts-queue-dlq",
        'to_queue': "panther-alerts-queue",
        'region': "us-west-2",
    }
    main(params)
