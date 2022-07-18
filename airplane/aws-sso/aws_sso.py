from pyshared.dynamo_db import DynamoDbSearch, get_ddb_table
from pyshared.date_utils import generate_utc_timestamp, generate_utc_expiry_timestamp


def write_to_db(table, data_to_write):
    extra_fields = {'request_time': generate_utc_timestamp(), 'request_status': 'NEW'}
    response = table.put_item(Item={**data_to_write, **extra_fields})
    return response


def check_valid_expiry_time(expiry_time):
    if not 1 <= int(expiry_time) <= 4:
        raise ValueError(
                    f"Invalid expiry time provided: {expiry_time} not one of the valid values of [1,2,3,4]"
                )


def check_valid_permission_set(permission_set):
    possible_permission_set = {'panther-ops', 'panther-viewonly', 'panther-billing', 'panther-billingadmin', 'panther-readsfsecret'}
    if permission_set not in possible_permission_set:
        raise ValueError(
                    f"Invalid permission set was specified: {permission_set}"
                )


def main(params):
    check_valid_expiry_time(params['expiry_time'])
    check_valid_permission_set(params['permission_set'])

    table_name = "escalation-requests"
    role_arn = "arn:aws:iam::945083323154:role/AirplaneDynamoDBWrite"
    table = get_ddb_table(table_name=table_name, arn=role_arn, region='us-west-2')

    expiry_time = int(params['expiry_time'])
    params['expiry_time'] = generate_utc_expiry_timestamp(expiry_time)

    return write_to_db(table, params)
