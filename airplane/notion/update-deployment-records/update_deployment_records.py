# Linked to https://app.airplane.dev/t/update_panther_deployments_notion_record [do not edit this line]
import datetime
import re
import urllib.parse

from notion.customer_info_retriever import AllCustomerAccountsInfo
# from notion.databases import create_rtf_value
from pyshared.git_ops import git_clone

EMPTY_FIELD = ""
IGNORE_FIELD = None


def get_version_number(template_url: str, existing_notion_version: str) -> str:
    if existing_notion_version == "Not Created":
        return existing_notion_version
    return re.search("s3.amazonaws.com/(.+?)/panther.yml", template_url).group(1).lstrip("v")


def standardize_deploy_group(deploy_group: str) -> str:
    if deploy_group is None:
        return deploy_group

    return {
        "cpaas": "CPaaS",
        "hold": "hold",
        "internal": "Internal",
        "legacy-sf": "legacy-sf"
    }.get(deploy_group.lower(), deploy_group.upper())


def get_expected_customer_attributes(account_info):
    aws_account_id = account_info.dynamo_info.get("AWSConfiguration", {}).get("AccountId", IGNORE_FIELD)
    # try:
    #    company_name = account_info.dynamo_info["CompanyDisplayName"]
    # except KeyError:
    #    company_name = account_info.deploy_yml_info["CloudFormationParameters"]["CompanyDisplayName"]
    region = account_info.dynamo_info['GithubConfiguration']['CustomerRegion']
    # role_name = f"PantherSupportRole-{region}"
    # url_support_name = urllib.parse.quote(f"{company_name} Support")

    expected_attrs = {
        # Ignoring AWS_Organization
        # Ignoring Backend
        "Deploy_Group": standardize_deploy_group(account_info.deploy_yml_info.get("DeploymentGroup")),
        # Ignoring Deploy Type
        "Email": f"panther-hosted+{account_info.fairytale_name}@panther.io",
        # Ignoring Legacy_Stacks
        # Ignoring Name
        # Ignoring PoC
        "Region": region,
        # Ignoring Service_Type
        "Upgraded": account_info.dynamo_info["Updated"],
        "Version": get_version_number(account_info.dynamo_info["PantherTemplateURL"],
                                      account_info.notion_info.Version),
    }

    if aws_account_id != IGNORE_FIELD:
        expected_attrs["AWS_Account_ID"] = aws_account_id
    #    expected_attrs["Support_Role"] = create_rtf_value(
    #        text=role_name,
    #        url=(f"https://{region}.signin.aws.amazon.com/switchrole?roleName={role_name}&account={aws_account_id}&"
    #             f"displayName={url_support_name}")
    #    )
    return expected_attrs


def needs_update(attr, notion_val, update_val):
    if update_val is IGNORE_FIELD:
        return False

    if attr == "Upgraded" and str(notion_val) and update_val:
        # Notion and/or notional doesn't maintain the seconds when parsing the page.
        # Remove seconds, then compare for equality
        notion_no_seconds = datetime.datetime.strptime(":".join(str(notion_val).split(":", 2)[:-1]), "%Y-%m-%d %H:%M")
        dynamo_no_seconds = datetime.datetime.strptime(update_val.rsplit(":", 1)[0], "%Y-%m-%dT%H:%M")
        return notion_no_seconds != dynamo_no_seconds

    return notion_val != update_val


def main(params):
    hosted_deploy_dir = (params["hosted_deploy_dir"] if "hosted_deploy_dir" in params
                         else git_clone(repo="hosted-deployments", github_setup=True))
    all_accounts = AllCustomerAccountsInfo(hosted_deploy_dir=hosted_deploy_dir)

    print(f"Accounts that will be skipped due to not existing in Notion, Dynamo, or hosted-deployments:\n"
          f"{all_accounts.uncommon_fairytale_names}")

    for account_info in all_accounts:
        expected_attrs = get_expected_customer_attributes(account_info)
        for attr in expected_attrs:
            current_val, update_val = getattr(account_info.notion_info, attr), expected_attrs[attr]
            if needs_update(attr, current_val, update_val):
                print(f"{attr} will be updated for {account_info.fairytale_name}:\n{current_val} -> {update_val}\n\n")
                setattr(account_info.notion_info, attr, update_val)
        account_info.notion_info.commit()
