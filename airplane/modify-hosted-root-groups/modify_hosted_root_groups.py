# Linked to https://app.airplane.dev/t/modify_hosted_root_groups_zav [do not edit this line]

from pyshared.aws_creds import get_assumed_role_creds
from pyshared.git_ops import git_add, git_clone, git_commit, git_push
from ruamel.yaml import YAML
from ruamel.yaml.comments import TaggedScalar
import boto3, os

REPOSITORY = "hosted-aws-management"
GROUPS_FILE_PATH = "panther-hosted-root/us-west-2/panther-hosted-root-groups.yml"
CLOUDFORMATION_READ_ONLY_ROLE_ARN = os.environ.get("CLOUDFORMATION_READ_ONLY_ROLE_ARN",
                                                   "arn:aws:iam::255674391660:role/AirplaneCloudFormationReadOnly")
REGION = os.environ.get("AWS_REGION", "us-west-2")


def get_cloudformation_export_name(username):
    credentials = get_assumed_role_creds(arn=CLOUDFORMATION_READ_ONLY_ROLE_ARN, desc="cfn_list_exports")['Credentials']
    client = boto3.client(
        'cloudformation',
        region_name=REGION,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )

    response = client.list_exports()
    exports = response["Exports"]
    while "NextToken" in response:
        response = client.list_exports(NextToken=response["NextToken"])
        exports.extend(response["Exports"])
    for export in exports:
        if export['Value'] == username:
            return export['Name']
    raise Exception(f'No Cloudformation export found for user "{username}"')


def group_resource_name(data, group):
    for key, value in data['Resources'].items():
        if value['Type'] == 'AWS::IAM::Group' and value['Properties']['GroupName'] == group:
            return key


def group_membership_resource_name(data, group):
    group_name = group_resource_name(data, group)
    for key, value in data['Resources'].items():
        if value['Type'] == 'AWS::IAM::UserToGroupAddition' and value['Properties']['GroupName'].value == group_name:
            return key


def get_group_membership_list(data, group):
    group_membership_key = group_membership_resource_name(data, group)
    return data['Resources'][group_membership_key]['Properties']['Users']


def add_user_to_group(data, params):
    group_members = get_group_membership_list(data, params["group"])

    user_import_value = TaggedScalar(tag='!ImportValue', value=get_cloudformation_export_name(params["aws_username"]))
    group_members.append(user_import_value)

    if params["temporary"]:
        params["reason"] = f'Temporary: {params["reason"]} Expires: {params["expires"]}'
    group_members.yaml_add_eol_comment(params["reason"], len(group_members) - 1)


def remove_user_from_group(data, params):
    group = params["group"]
    username = params["aws_username"]
    cloudformation_export_name = get_cloudformation_export_name(username)

    group_members = get_group_membership_list(data, group)

    for member in group_members:
        if member.value == cloudformation_export_name:
            group_members.remove(member)
            return
    raise Exception(f'Error: user "{username}" not found in group "{group}"')


def main(params):
    if (params["add_or_remove"] == "Add") and params.get("temporary", True) and (not params.get("expires")):
        raise Exception("Expiration must be set if access is temporary")

    repository_dir = (params["hosted_aws_management_dir"] if "hosted_aws_management_dir" in params
                      else git_clone(repo=REPOSITORY, github_setup=os.environ.get("DEPLOY_KEY_BASE64")))

    data_path = os.path.join(repository_dir, GROUPS_FILE_PATH)

    yaml = YAML(pure=True)
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(data_path, 'r') as file:
        cfn_yaml = yaml.load(file)

    operation = params["add_or_remove"]

    if operation == "Add":
        add_user_to_group(cfn_yaml, params)
    elif operation == "Remove":
        remove_user_from_group(cfn_yaml, params)
    else:
        raise Exception(f'Unexpected value for operation: ${operation}')

    with open(data_path, 'w') as file:
        yaml.dump(cfn_yaml, file)

    os.chdir(repository_dir)
    git_add([GROUPS_FILE_PATH])
    git_commit(f"{operation}s {params['aws_username']} to/from {params['group']}")
    git_push(test_run=params["airplane_test_run"])
