from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from botocore.exceptions import ClientError


def get_delete_stack_role_arn(organization: str) -> str:
    if organization == "root":
        return get_aws_const("ROOT_CFN_DELETE_STACK_ROLE_ARN")
    elif organization == "hosted":
        return get_aws_const("HOSTED_CFN_DELETE_STACK_ROLE_ARN")
    raise AttributeError(f"Role doesn't exist in {organization}.")


def delete_dns_records(organization: str, fairytale_name: str) -> None:
    cfn_kwargs = {
        "service_name": "cloudformation",
        "arns": get_delete_stack_role_arn(organization),
        "desc": f"cfn_remove_dns_records",
        "region": "us-west-2"
    }
    cfn_client = get_credentialed_client(**cfn_kwargs)
    cfn_waiter = cfn_client.get_waiter("stack_delete_complete")

    stack_names = [f"route53-{fairytale_name}", f"panther-cert-{fairytale_name}"]
    for stack_name in stack_names:
        try:
            # Try to find the stack by name, raises an error if doesn't exist
            cfn_client.describe_stacks(StackName=stack_name)
            cfn_client.delete_stack(StackName=stack_name)
            cfn_waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 30, "MaxAttempts": 20})
            print(f"Deleted '{stack_name}' stack.")
        except ClientError:
            print(f"Stack {stack_name} doesn't exist or is already deleted.")


def main(params):
    delete_dns_records(organization=params["organization"], fairytale_name=params["fairytale_name"])
