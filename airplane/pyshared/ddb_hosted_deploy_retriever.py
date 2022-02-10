import os

from pyshared.dynamo_db import get_ddb_table, recursive_get_from_dynamodb_result
from pyshared.dynamo_db_tables import HOSTED_DEPLOYMENTS_METADATA


class DdbHostedDeployAccountInfo:

    def __init__(self, fairytale_name, ddb_arn, ddb_region):
        table = get_ddb_table(table_name=HOSTED_DEPLOYMENTS_METADATA, arn=ddb_arn, region=ddb_region)
        self.account_info = table.get_item(Key={"CustomerId": fairytale_name})["Item"]

    def get_customer_attr(self, attr):
        query_result_keys = {
            "region": ("GithubConfiguration", "CustomerRegion"),
            "aws_account_id": ("AWSConfiguration", "AccountId")
        }.get(attr)

        if not query_result_keys:
            raise ValueError(f"Unknown customer attribute to retrieve: {attr}")

        return recursive_get_from_dynamodb_result(dynamodb_result=self.account_info,
                                                  dynamodb_item_keys=query_result_keys)
