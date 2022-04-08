import os

from pyshared.aws_creds import get_credentialed_client

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
    return get_credentialed_client(service_name="cloudformation", region=REGION, arns=role_arn, desc="cfn_list_exports")


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


def get_group_policies(data, resourse):
    for key, value in data['Resources'].items():
        if value['Type'] == 'AWS::IAM::Group' and key == resourse:
            return value['Properties']['Policies']


def get_group_policy_statements(data, resource, policy_name):
    policies = get_group_policies(data, resource)
    for policy in policies:
        if policy['PolicyName'] == policy_name:
            return policy['PolicyDocument']['Statement']
