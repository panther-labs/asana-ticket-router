import boto3
import json


def get_secret_value(secret_name: str) -> str:
    """Get the first value from an AWS key-value pair."""
    secret = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=secret_name)["SecretString"])
    return list(secret.values())[0]
