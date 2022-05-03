import boto3
import json
import os


def _get_env_var(secret_name: str) -> str:
    """
    For local testing, define the secret as an environment variable and it will bypass getting it from AWS.
    Example of variable name: airplane/notion-auth-token would be NOTION_AUTH_TOKEN as an environment variable
    """
    env_var_name = secret_name.replace("airplane/", "").upper().replace("-", "_")
    return os.getenv(env_var_name)


def get_secret_value(secret_name: str) -> str:
    """Get the first value from an AWS key-value pair."""
    secret = _get_env_var(secret_name=secret_name)
    if secret:
        return secret

    secret = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=secret_name)["SecretString"])
    return list(secret.values())[0]
