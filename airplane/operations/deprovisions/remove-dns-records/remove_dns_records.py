from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client, get_credentialed_resource


def main(params):
    name = params["fairytale_name"]
    stack_names = (f"route53-{name}", f"panther-cert-{name}")
    waiter_cfg = {"Delay": 30, "MaxAttempts": 20}
    cfn_kwargs = {
        "service_name": "cloudformation",
        "arns": get_aws_const("CLOUDFORMATION_DELETE_STACK_ROLE_ARN"),
        "desc": f"cfn_remove_{name}_route",
        "region": "us-west-2"
    }

    cfn_resource = get_credentialed_resource(**cfn_kwargs)
    [cfn_resource.Stack(stack_name).delete() for stack_name in stack_names]

    [
        get_credentialed_client(**cfn_kwargs).get_waiter("stack_delete_complete").wait(StackName=stack_name,
                                                                                       WaiterConfig=waiter_cfg)
        for stack_name in stack_names
    ]
