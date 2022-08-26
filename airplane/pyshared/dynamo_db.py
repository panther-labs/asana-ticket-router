import os
import tenacity

from boto3.dynamodb.conditions import Key
from functools import reduce

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_resource

DYNAMO_REGION = get_aws_const("HOSTED_DYNAMO_RO_ROLE_REGION")
POLL_FREQUENCY_SECS = int(os.environ.get("POLL_FREQUENCY_SECONDS", 60))
POLL_TIMEOUT_SECS = int(os.environ.get("POLL_TIMEOUT_SECONDS", 900))


def print_before_query(retry_state):
    key = retry_state.kwargs["partition_key"]
    val = retry_state.kwargs["partition_value"]
    result_keys = " -> ".join(retry_state.kwargs["query_result_keys"])
    print(f"""Attempt number {retry_state.attempt_number}, seconds waited: {retry_state.idle_for}:
Querying to get [{key} == {val}] from DynamoDB, then getting {result_keys} from the result (until non-empty)
""")


def raise_exception_after_query_fails(retry_state):
    raise RuntimeError("Polling for DynamoDB query failed")


def get_ddb_table(table_name, arn=None, region=None, test_role=None):
    dynamo_db = get_credentialed_resource(service_name="dynamodb",
                                          arns=arn,
                                          desc="dynamo_db",
                                          region=DYNAMO_REGION if region is None else region,
                                          test_role=test_role)
    return dynamo_db.Table(table_name)


def recursive_get_from_dynamodb_result(dynamodb_result, dynamodb_item_keys):
    return reduce(lambda reduce_dict, reduce_key: reduce_dict.get(reduce_key, {}), dynamodb_item_keys, dynamodb_result)


class DynamoDbSearch:

    def __init__(self, table_name, arn=None, region=None, test_role=None):
        self.table = get_ddb_table(table_name=table_name, arn=arn, region=region, test_role=test_role)

    @tenacity.retry(before=print_before_query,
                    retry=tenacity.retry_if_result(lambda desired_val: not bool(desired_val)),
                    retry_error_callback=raise_exception_after_query_fails,
                    stop=tenacity.stop_after_delay(POLL_TIMEOUT_SECS),
                    wait=tenacity.wait_fixed(POLL_FREQUENCY_SECS))
    def poll_until_available(self, partition_key, partition_value, query_result_keys):
        query_item = self.get_query_item(partition_key, partition_value)
        return recursive_get_from_dynamodb_result(query_item, query_result_keys)

    def scan_and_organize_result(self, scan_result_keys=None):
        """Scan the table and create a new dict result, with the keys being the value of query_result_keys."""
        scan_result = self.table.scan()

        if scan_result_keys is None:
            return scan_result

        organized_scan_result = {}
        for item in scan_result["Items"]:
            key = recursive_get_from_dynamodb_result(item, scan_result_keys)
            if key:
                organized_scan_result[key] = item
        return organized_scan_result

    def get_query_item(self, key, val):
        dynamo_filter = Key(key).eq(val)
        query_result = self.table.query(KeyConditionExpression=dynamo_filter)

        if query_result["Count"] > 1:
            raise RuntimeError(f"Found more than one query result for key '{key}' and value '{val}':"
                               f"{query_result}")

        return {} if query_result["Count"] == 0 else query_result["Items"][0]
