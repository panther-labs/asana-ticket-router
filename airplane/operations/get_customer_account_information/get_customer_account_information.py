from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.ddb_hosted_deploy_retriever import DdbHostedDeployAccountInfo

DYNAMO_RO_ROLE_ARN = get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_ARN")
ORGANIZATIONS_RO_ROLE_ARN = get_aws_const(const_name="ORGANIZATIONS_RO_ROLE_ARN")


def get_fairytale_name_by_account_id(aws_account_id: str) -> str:
    client_kwargs = {
        "service_name": "organizations",
        "arns": ORGANIZATIONS_RO_ROLE_ARN,
        "desc": f"organizations_get_fairytale_name",
    }
    client = get_credentialed_client(**client_kwargs)
    response = client.describe_account(AccountId=aws_account_id)
    # Some older accounts have "panther-hosted-" prefix in their AWS account name
    return response['Account']['Name'].removeprefix("panther-hosted-")


def get_customer_info(fairytale_name: str) -> dict:
    account_info = DdbHostedDeployAccountInfo(fairytale_name=fairytale_name, ddb_arn=DYNAMO_RO_ROLE_ARN)
    return {
        "fairytale_name": fairytale_name,
        "aws_account_id": account_info.get_customer_attr(attr="aws_account_id"),
        "region": account_info.get_customer_attr(attr="region")
    }


def main(params: dict) -> dict:
    # Check if both params are empty
    if not params.get("aws_account_id") and not params.get("fairytale_name"):
        raise AttributeError("Either 'AWS Account ID' or 'Fairytale Name' must be provided.")

    # Check if both params were provided
    if params.get("aws_account_id") and params.get("fairytale_name"):
        raise AttributeError("Only 'AWS Account ID' or 'Fairytale Name' must be provided.")

    if params.get("aws_account_id"):
        params["fairytale_name"] = get_fairytale_name_by_account_id(params["aws_account_id"])

    return get_customer_info(params["fairytale_name"])
