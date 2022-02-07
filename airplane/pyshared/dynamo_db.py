import boto3
import os
import tenacity

from boto3.dynamodb.conditions import Key
from functools import reduce

from pyshared.aws_creds import get_credentialed_client

DYNAMO_REGION = os.environ.get("DYNAMO_REGION", "us-west-2")
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


class DynamoDbSearch:

    def __init__(self, table_name, arn=None, region=None):
        dynamo_db = get_credentialed_client(service_name="dynamodb",
                                            arn=arn,
                                            desc="dynamo_db",
                                            region=DYNAMO_REGION if region is None else region)
        self.table = dynamo_db.Table(table_name)

    @tenacity.retry(before=print_before_query,
                    retry=tenacity.retry_if_result(lambda desired_val: not bool(desired_val)),
                    retry_error_callback=raise_exception_after_query_fails,
                    stop=tenacity.stop_after_delay(POLL_TIMEOUT_SECS),
                    wait=tenacity.wait_fixed(POLL_FREQUENCY_SECS))
    def poll_until_available(self, partition_key, partition_value, query_result_keys):
        return self._recursive_get_from_dynamodb_result(self._get_query_item(partition_key, partition_value),
                                                        query_result_keys)

    def scan_and_organize_result(self, scan_result_keys=None):
        """Scan the table and create a new dict result, with the keys being the value of query_result_keys."""
        scan_result = self.table.scan()

        if scan_result_keys is None:
            return scan_result

        organized_scan_result = {}
        for item in scan_result["Items"]:
            key = self._recursive_get_from_dynamodb_result(item, scan_result_keys)
            if key:
                organized_scan_result[key] = item
        return organized_scan_result

    def _get_query_item(self, key, val):
        dynamo_filter = Key(key).eq(val)
        query_result = self.table.query(KeyConditionExpression=dynamo_filter)

        if query_result["Count"] > 1:
            raise RuntimeError(f"Found more than one query result for key '{key}' and value '{val}':"
                               f"{query_result}")

        return {} if query_result["Count"] == 0 else query_result["Items"][0]

    @staticmethod
    def _recursive_get_from_dynamodb_result(dynamodb_result, dynamodb_item_keys):
        return reduce(lambda reduce_dict, reduce_key: reduce_dict.get(reduce_key, {}), dynamodb_item_keys,
                      dynamodb_result)
