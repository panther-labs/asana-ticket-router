from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client


def get_teardown_role_arns(organization: str, aws_account_id: str):
    if organization == "root":
        return f"arn:aws:iam::{aws_account_id}:role/PantherTeardownRole"
    elif organization == "hosted":
        return get_aws_const(const_name="HOSTED_TEARDOWN_ROLE_ARN"), \
               f"arn:aws:iam::{aws_account_id}:role/PantherTeardownRole"
    raise AttributeError(f"Org role doesn't exist in {organization}.")


def delete_all_stacks(organization: str, aws_account_id: str, region: str, is_dry_run: bool):
    cfn_kwargs = {
        "service_name": "cloudformation",
        "arns": get_teardown_role_arns(organization, aws_account_id),
        "desc": f"cfn_remove_master_and_custom_stacks",
        "region": region,
    }
    cfn_client = get_credentialed_client(**cfn_kwargs)

    response = cfn_client.list_stacks()
    stacks_to_delete = [s["StackName"] for s in response["StackSummaries"]
                        # Filter out deleted stacks
                        if s["StackStatus"] not in ["DELETE_COMPLETE", "DELETE_IN_PROGRESS"]
                        # Filter out stack instances
                        and not s["StackName"].startswith("StackSet-")
                        # Filter out nested stacks
                        and s.get("ParentId") is None]

    if not stacks_to_delete:
        print("No stacks to delete found. Exiting.")
        return

    for stack in stacks_to_delete:
        if is_dry_run:
            print(f"Dry run: will not be deleting '{stack}' stack.")
        else:
            print(f"Deleting '{stack}' stack.")
            cfn_client.delete_stack(StackName=stack)


def main(params):
    delete_all_stacks(organization=params["organization"],
                      aws_account_id=params["aws_account_id"],
                      region=params["region"],
                      is_dry_run=params["is_dry_run"])
