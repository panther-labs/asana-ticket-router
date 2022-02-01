import boto3
import os
from pyshared.aws_creds import get_assumed_role_creds

REGION = os.environ.get("AWS_REGION", "us-west-2")


def get_group_membership_list(data, group):
    group_membership_key = group_membership_resource_name(data, group)
    return data['Resources'][group_membership_key]['Properties']['Users']


def group_membership_resource_name(data, group):
    group_name = group_resource_name(data, group)
    for key, value in data['Resources'].items():
        if value['Type'] == 'AWS::IAM::UserToGroupAddition' and value['Properties']['GroupName'].value == group_name:
            return key


def group_resource_name(data, group):
    for key, value in data['Resources'].items():
        if value['Type'] == 'AWS::IAM::Group' and value['Properties']['GroupName'] == group:
            return key


def group_name_from_resource(data, resource):
    for key, value in data['Resources'].items():
        if key == resource:
            return value['Properties']['GroupName']


def _create_cloudformation_client(role_arn):
    credentials = get_assumed_role_creds(arn=role_arn, desc="cfn_list_exports")['Credentials']
    client = boto3.client(
        'cloudformation',
        region_name=REGION,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )
    return client


def list_exports(role_arn):
    client = _create_cloudformation_client(role_arn)

    response = client.list_exports()
    exports = response["Exports"]
    while "NextToken" in response:
        response = client.list_exports(NextToken=response["NextToken"])
        exports.extend(response["Exports"])
    return exports


def get_cloudformation_export_name(username, role_arn):
    for export in list_exports(role_arn):
        if export['Value'] == username:
            return export['Name']
    raise Exception(f'No Cloudformation export found for user "{username}"')


def get_cloudformation_export_value(export_name, role_arn):
    for export in list_exports(role_arn):
        if export['Name'] == export_name:
            return export['Value']
    raise Exception(f'No Cloudformation export found for "{export_name}"')