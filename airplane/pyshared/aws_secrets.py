import json
import os
from typing import List, Optional

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client


def _get_env_var(secret_name: str) -> str:
    """
    For local testing, define the secret as an environment variable and it will bypass getting it from AWS.
    Example of variable name: airplane/notion-auth-token would be NOTION_AUTH_TOKEN as an environment variable
    """
    env_var_name = secret_name.replace("airplane/", "").upper().replace("-", "_")
    return os.environ.get(env_var_name)


def _get_secret(secret_name: str, arns: Optional[str | List[str]] = None, region: str = None) -> dict:
    secret = _get_env_var(secret_name=secret_name)
    if secret:
        return secret

    secrets_client = get_credentialed_client(service_name="secretsmanager",
                                             arns=arns,
                                             desc=f"retrieve_secret",
                                             region=region)

    return json.loads(secrets_client.get_secret_value(SecretId=secret_name)["SecretString"])


def get_secret_value(secret_name: str) -> str:
    """Get the first value from an AWS key-value pair."""
    # TODO: Make this a part of the AirplaneTask class and fail if a local run and it doesn't get env var
    secret = _get_secret(secret_name=secret_name)
    return list(secret.values())[0]


def get_snowflake_account_admin_secret():
    """Requires the task to use the AirplaneWorkers-ReadSnowflakeMasterCredentials ECS role."""
    return _get_secret(secret_name=get_aws_const("SNOWFLAKE_ACCOUNT_ADMIN_SECRET_ARN"),
                       arns=get_aws_const("SNOWFLAKE_ACCOUNT_ADMIN_SECRET_READ_ROLE"),
                       region="us-west-2")
