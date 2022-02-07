import boto3


def get_assumed_role_creds(arn, desc="task"):
    if arn:
        return boto3.client("sts").assume_role(
            RoleArn=arn, RoleSessionName=f"airplane_workers_{desc}")
    return None


def get_credentialed_client(service_name, arn, desc, region=None):
    creds = get_assumed_role_creds(arn=arn, desc=desc)

    kwargs = {"service_name": service_name}

    if creds:
        kwargs.update({
            "aws_access_key_id": creds["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": creds["Credentials"]["SecretAccessKey"],
            "aws_session_token": creds["Credentials"]["SessionToken"]
        })

    if region is not None:
        kwargs["region_name"] = region

    return boto3.client(**kwargs)

    return sts_conn.assume_role(
        RoleArn=hosted_root_arn,
        RoleSessionName="airplane_productivity",
    )