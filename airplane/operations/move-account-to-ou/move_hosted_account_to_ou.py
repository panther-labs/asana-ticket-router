from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.hosted_orgs import HostedOrgs

ORG_MOVE_ACCOUNT_ROLE_ARN = get_aws_const("ORG_MOVE_ACCOUNT_ROLE_ARN")


def move_account_to_ou(fairytale_name: str, aws_account_id: str, target_ou_name: str, test_run: bool) -> None:
    org_client = get_credentialed_client(service_name="organizations",
                                         arns=ORG_MOVE_ACCOUNT_ROLE_ARN,
                                         desc=f"org_move_{fairytale_name}_to_{target_ou_name}")
    parent_ou_ids = [parent_ou["Id"] for parent_ou in org_client.list_parents(ChildId=aws_account_id)["Parents"]]
    if len(parent_ou_ids) != 1:
        raise RuntimeError(f"{fairytale_name} does not have exactly 1 parent: {parent_ou_ids}")

    current_ou_id = parent_ou_ids[0]
    current_ou = org_client.describe_organizational_unit(OrganizationalUnitId=current_ou_id)["OrganizationalUnit"]

    target_ou_id = HostedOrgs.get_ou_id(ou_name=target_ou_name)
    target_ou = org_client.describe_organizational_unit(OrganizationalUnitId=target_ou_id)["OrganizationalUnit"]

    log_msg = f"{aws_account_id} ({fairytale_name}) from {current_ou['Name']} to {target_ou['Name']}"

    if test_run:
        print(f"Testing - will not move {log_msg}")
    else:
        print(f"Moving {log_msg}")
        org_client.move_account(AccountId=aws_account_id,
                                SourceParentId=current_ou["Id"],
                                DestinationParentId=target_ou["Id"])


def main(params: dict) -> None:
    move_account_to_ou(fairytale_name=params["fairytale_name"],
                       aws_account_id=params["aws_account_id"],
                       target_ou_name=params["target_ou"],
                       test_run=params["airplane_test_run"])
