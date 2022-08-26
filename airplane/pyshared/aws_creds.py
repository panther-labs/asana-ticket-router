import boto3

from pyshared.airplane_utils import is_local_run
from pyshared.local_aws_role_exec import aws_vault_exec, input_mfa


def _get_creds(arns, test_role=None, desc="task"):
    if is_local_run():
        if arns and (test_role is None):
            raise RuntimeError("Assuming roles with a local_run requires test roles to be set when getting "
                               "credentialed resources or clients")
        return _get_creds_from_aws_vault(aws_profile=test_role[0], region=test_role[1])
    else:
        return _get_assumed_role_creds(arns=arns, desc=desc)


def _get_creds_from_aws_vault(aws_profile, region):
    input_mfa(aws_profile=aws_profile, region=region)
    output = aws_vault_exec(aws_profile=aws_profile, region=region, cmd="env")
    env_vars = {key: value for key, value in (line.split("=", 1) for line in output.split("\n") if line)}

    return {
        "Credentials": {
            "AccessKeyId": env_vars["AWS_ACCESS_KEY_ID"],
            "SecretAccessKey": env_vars["AWS_SECRET_ACCESS_KEY"],
            "SessionToken": env_vars["AWS_SESSION_TOKEN"]
        }
    }


def _get_assumed_role_creds(arns, desc="task", creds=None):
    """Recursively assume roles, starting the first in the arns tuple. Each consecutive call will use credentials from
    the previous function call.
    :param arns: Tuple of arns to assume
    :param desc: The description to give the AWS client
    :param creds: Credentials from roles assumed during previous calls
    :return: The dictionary credentials for a desired role
    """
    if arns:
        sts_client = boto3.client(**_get_kwargs(service_name="sts", creds=creds))
        creds = sts_client.assume_role(RoleArn=arns[0], RoleSessionName=f"airplane_workers_{desc}")
        return _get_assumed_role_creds(arns=arns[1:], desc=desc, creds=creds)
    return creds


def _get_kwargs(service_name, region=None, creds=None):
    kwargs = {"service_name": service_name}

    if creds:
        kwargs.update({
            "aws_access_key_id": creds["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": creds["Credentials"]["SecretAccessKey"],
            "aws_session_token": creds["Credentials"]["SessionToken"]
        })

    if region is not None:
        kwargs["region_name"] = region

    return kwargs


def _convert_arns_to_tuple(arns):
    return {str: (arns, ), None: tuple()}.get(type(arns), arns)


def get_credentialed_client(service_name, arns, desc, region=None, test_role=None):
    """Get a client to a service that has assumed a role.

    :param service_name: Name of service to assume, such as "lambda"
    :param arns: A string or tuple of ARNs, such as ("arn1", "arn2"), "arn", or None.
                 Roles will be assumed sequentially, so order matters
    :param desc: The description to give the AWS client
    :param region: Region of the service
    :param test_role: The role to use from aws-vault (instead of the ARNs) for testing purposes
    :return: Client for an AWS service
    """
    creds = _get_creds(arns=_convert_arns_to_tuple(arns), test_role=test_role, desc=desc)
    return boto3.client(**_get_kwargs(service_name=service_name, region=region, creds=creds))


def get_credentialed_resource(service_name, arns, desc, region=None, test_role=None):
    creds = _get_creds(arns=_convert_arns_to_tuple(arns), test_role=test_role, desc=desc)
    return boto3.resource(**_get_kwargs(service_name=service_name, region=region, creds=creds))
