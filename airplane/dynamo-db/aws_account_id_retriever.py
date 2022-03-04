# Linked to https://app.airplane.dev/t/get_from_dynamo_db [do not edit this line]
from pyshared.aws_consts import get_aws_const
from pyshared.dynamo_db import DynamoDbSearch


def main(params):
    if params["airplane_test_run"]:
        # In a test run, we still want to retrieve something from DynamoDB to make sure that works. We also want
        # to make sure it is for a customer that already exists... so hardcode it to an already-existing customer
        params["fairytale_name"] = "king-of-spades-v2"

    db_search = DynamoDbSearch(table_name=get_aws_const(const_name="HOSTED_DEPLOYMENTS_METADATA"),
                               arn=get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_ARN"))

    return {
        "aws_account_id":
        db_search.poll_until_available(partition_key="CustomerId",
                                       partition_value=params["fairytale_name"],
                                       query_result_keys=("AWSConfiguration", "AccountId"))
    }
