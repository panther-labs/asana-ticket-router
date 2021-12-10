import boto3
import os

from dynamo_db import DynamoDbQuery

DYNAMO_AWS_ID = os.environ.get("DYNAMO_AWS_ID")
DYNAMO_ROLE_NAME = os.environ.get("DYNAMO_ROLE_NAME")


def get_assumed_role_creds():
    if DYNAMO_AWS_ID and DYNAMO_ROLE_NAME:
        return boto3.client("sts").assume_role(
            RoleArn=f"arn:aws:iam::{DYNAMO_AWS_ID}:role/{DYNAMO_ROLE_NAME}",
            RoleSessionName="airplane_workers_aws_id_retriever"
        )
    return None


def retrieve_info(fairytale_name, customer_query_keys):
    query = DynamoDbQuery(
        table_name="hosted-deployments-DeploymentMetadataTable-22PITRD2LM2B",
        assumed_role_creds=get_assumed_role_creds()
    )

    return query.poll_until_available(
        partition_key="CustomerId",
        partition_value=fairytale_name,
        query_result_keys=customer_query_keys
    )
