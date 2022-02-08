import boto3


def _get_assumed_role_creds(arns, desc="task", creds=None):
    """Recursively assume roles, starting the first in the arns tuple. Each consecutive call will use credentials from
    the previous function call.
    :param arns: Tuple of arns to assume
    :param desc: The description to give the AWS client
    :param creds: Credentials from roles assuemd during previous calls
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


def get_credentialed_client(service_name, arns, desc, region=None):
    """Get a client to a service that has assumed a role.

    :param service_name: Name of service to assume, such as "lambda"
    :param arns: A string or tuple of ARNs, such as ("arn1", "arn2"), "arn", or None.
                 Roles will be assumed sequentially, so order matters
    :param desc: The sescription to give the AWS client
    :param region: Region of the service
    :return: Client for an AWS service
    """
    return boto3.client(**_get_kwargs(service_name=service_name,
                                      region=region,
                                      creds=_get_assumed_role_creds(arns=_convert_arns_to_tuple(arns), desc=desc)))


def get_credentialed_resource(service_name, arns, desc, region=None):
    return boto3.resource(**_get_kwargs(service_name=service_name,
                                        region=region,
                                        creds=_get_assumed_role_creds(arns=_convert_arns_to_tuple(arns), desc=desc)))
