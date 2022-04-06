from pyshared.customer_info_retriever import AllCustomerAccountsInfo
from pyshared.git_ops import git_clone


def main(params):
    hosted_deploy_dir = git_clone(repo="hosted-deployments",
                                  github_setup=True,
                                  existing_dir=params.get("hosted_deploy_dir"))
    info = AllCustomerAccountsInfo(hosted_deploy_dir=hosted_deploy_dir).get_account_info(params["fairytale_name"])
    cfn = info.deploy_yml_info["CloudFormationParameters"]
    ddb_aws = info.dynamo_info["AWSConfiguration"]

    return {
        "account_id": ddb_aws["AccountId"],
        "customer_name": cfn["CompanyDisplayName"],
        "domain": cfn["CustomDomain"]
    }
