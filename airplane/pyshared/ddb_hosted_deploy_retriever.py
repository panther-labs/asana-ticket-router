import os

from pyshared.aws_consts import get_aws_const
from pyshared.dynamo_db import get_ddb_table, recursive_get_from_dynamodb_result


class DdbHostedDeployAccountInfo:

    def __init__(self, fairytale_name, ddb_arn, ddb_region):
        table = get_ddb_table(table_name=get_aws_const(const_name="HOSTED_DEPLOYMENTS_METADATA"),
                              arn=ddb_arn,
                              region=ddb_region)
        self.account_info = table.get_item(Key={"CustomerId": fairytale_name}).get("Item")
        if not self.account_info:
            raise ValueError(f"Customer '{fairytale_name}' was not found")

    def get_customer_attr(self, attr):
        query_result_keys = {
            "region": ("GithubConfiguration", "CustomerRegion"),
            "aws_account_id": ("AWSConfiguration", "AccountId")
        }.get(attr)

        if not query_result_keys:
            raise ValueError(f"Unknown customer attribute to retrieve: {attr}")

        return recursive_get_from_dynamodb_result(dynamodb_result=self.account_info,
                                                  dynamodb_item_keys=query_result_keys)
