# Linked to https://app.airplane.dev/t/get_from_dynamo_db [do not edit this line]
import boto3
import os
import sys

sys.path.append("..")
from dynamo_db import DynamoDbQuery  # noqa: E402

DYNAMO_AWS_ID = os.environ.get("DYNAMO_AWS_ID")
DYNAMO_ROLE_NAME = os.environ.get("DYNAMO_ROLE_NAME")
DYNAMO_REGION = os.environ.get("DYNAMO_REGION", "us-west-2")


def _get_assumed_role_creds():
    if DYNAMO_AWS_ID and DYNAMO_ROLE_NAME:
        return boto3.client("sts").assume_role(
            RoleArn=f"arn:aws:iam::{DYNAMO_AWS_ID}:role/{DYNAMO_ROLE_NAME}",
            RoleSessionName="airplane_workers_aws_id_retriever"
        )
    return None


def main(params):
    query = DynamoDbQuery(
        table_name="hosted-deployments-DeploymentMetadataTable-22PITRD2LM2B",
        assumed_role_creds=_get_assumed_role_creds(),
        region=DYNAMO_REGION
    )

    account_id = query.poll_until_available(
        partition_key="CustomerId",
        partition_value=params["fairytale_name"],
        query_result_keys=("AWSConfiguration", "AccountId")
    )

    return {"aws_id": account_id}


if __name__ == "__main__":
    print(main({"fairytale_name": sys.argv[1]}))
