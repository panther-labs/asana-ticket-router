import os
from pyshared.dynamo_db import DynamoDbSearch, get_ddb_table
from pyshared.date_utils import generate_utc_timestamp, generate_utc_expiry_timestamp


def write_to_db(table, data_to_write):
    extra_fields = {'user_id': os.getenv("AIRPLANE_REQUESTER_EMAIL"), 'request_time': generate_utc_timestamp(), 'request_status': 'NEW'}
    response = table.put_item(Item={**data_to_write, **extra_fields})
    return response


def check_valid_expiry_time(expiry_time):
    if not 1 <= int(expiry_time) <= 4:
        raise ValueError(
                    f"Invalid expiry time provided: {expiry_time} not one of the valid values (1 - 4)"
                )


def check_valid_permission_set(permission_set):
    possible_permission_set = {'panther-ops', 'panther-viewonly', 'panther-billing', 'panther-billingadmin', 'panther-readsfsecret', 
    'panther-dataadmin', 'panther-deployadmin', 'panther-orgadmin'}
    if permission_set not in possible_permission_set:
        raise ValueError(
                    f"Invalid permission set was specified: {permission_set}"
                )


def check_valid_env_airplane_requestor_email():
    if os.environ.get('AIRPLANE_REQUESTER_EMAIL') is None:
        raise ValueError(
            "AIRPLANE_REQUESTER_EMAIL environment variable not set, unable to complete task since no email address was supplied."
        )


def main(params):
    check_valid_expiry_time(params['expiry_time'])
    check_valid_permission_set(params['permission_set'])
    check_valid_env_airplane_requestor_email()

    table_name = "escalation-requests"
    role_arn = "arn:aws:iam::945083323154:role/AirplaneDynamoDBWrite"
    table = get_ddb_table(table_name=table_name, arn=role_arn, region='us-west-2')

    expiry_time = int(params['expiry_time'])
    params['expiry_time'] = generate_utc_expiry_timestamp(expiry_time)

    return write_to_db(table, params)
