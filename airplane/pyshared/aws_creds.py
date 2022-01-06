import boto3


def get_assumed_role_creds(arn, desc="task"):
    if arn:
        return boto3.client("sts").assume_role(RoleArn=arn, RoleSessionName=f"airplane_workers_{desc}")
    return None

