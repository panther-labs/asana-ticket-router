# Linked to https://app.airplane.dev/t/move_account_to_deactivated_ou [do not edit this line]
import os

from pyshared.aws_creds import get_credentialed_client
from pyshared.ddb_hosted_deploy_retriever import DdbHostedDeployAccountInfo

DYNAMO_REGION = os.environ.get("DYNAMO_REGION", "us-west-2")
DYNAMO_RO_ROLE_ARN = os.environ.get("DYNAMO_RO_ROLE_ARN")
ORG_ROLE_ARN = os.environ.get("ORG_ROLE_ARN")
ORG_REGION = os.environ.get("ORG_ROLE_REGION")


def get_aws_account_id(fairytale_name):
    account_info = DdbHostedDeployAccountInfo(fairytale_name=fairytale_name,
                                              ddb_arn=DYNAMO_RO_ROLE_ARN,
                                              ddb_region=DYNAMO_REGION)
    return account_info.get_customer_attr(attr="aws_account_id")


def move_aws_account_to_deactivated_ou(fairytale_name, aws_account_id, test_run):
    org_client = get_credentialed_client(service_name="organizations",
                                         arns=ORG_ROLE_ARN,
                                         desc="org_move_${fairytale_name}_terminated",
                                         region=ORG_REGION)
    parents = [parent["Id"] for parent in org_client.list_parents(ChildId=aws_account_id)["Parents"]]
    if len(parents) != 1:
        raise RuntimeError(f"{fairytale_name} does not have exactly 1 parent: {parents}")
    current_org = parents[0]

    terminated_org = "ou-1z3b-ew8ndwb0"
    from_org = org_client.describe_organizational_unit(OrganizationalUnitId=current_org)["OrganizationalUnit"]
    to_org = org_client.describe_organizational_unit(OrganizationalUnitId=terminated_org)["OrganizationalUnit"]
    msg = f"{aws_account_id} ({fairytale_name}) from {from_org['Name']} to {to_org['Name']}"

    if test_run:
        print(f"Testing - will not move {msg}")
    else:
        print(f"Moving {msg}")
        org_client.move_account(AccountId=aws_account_id,
                                SourceParentId=from_org["Id"],
                                DestinationParentId=to_org["Id"])


def main(params):
    raise RuntimeError("Production use of this task pending further discussion. Needs proper role to execute")
    move_aws_account_to_deactivated_ou(fairytale_name=params["fairytale_name"],
                                       aws_account_id=get_aws_account_id(params["fairytale_name"]),
                                       test_run=params["airplane_test_run"])
