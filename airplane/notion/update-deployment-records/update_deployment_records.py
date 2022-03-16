# Linked to https://app.airplane.dev/t/update_panther_deployments_notion_record [do not edit this line]
import datetime
import pytz
import re
import urllib.parse

from notion.customer_info_retriever import AllCustomerAccountsInfo
from pyshared.notion_databases import are_rtf_values_equal, create_date_time_value, create_rtf_value
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


def get_company_name(account_info):
    # For special cases, where the display name in Notion doesn't match what is in dynamo - we can override it by
    # filling in the Notes section of the Notion table entry
    notes = str(account_info.notion_info.Notes)
    name_key = "Name: "
    if name_key in notes:
        after_name_index = notes.index(name_key) + len(name_key)

        notes = notes[after_name_index:]
        return notes.split(",")[0]
    try:
        return account_info.dynamo_info["CompanyDisplayName"]
    except KeyError:
        return account_info.deploy_yml_info["CloudFormationParameters"]["CompanyDisplayName"]


def get_expected_customer_attributes(account_info):
    aws_account_id = account_info.dynamo_info.get("AWSConfiguration", {}).get("AccountId", IGNORE_FIELD)
    company_name = get_company_name(account_info)
    region = account_info.dynamo_info['GithubConfiguration']['CustomerRegion']
    upgraded_time_utc = pytz.timezone("UTC").localize(
        datetime.datetime.strptime(account_info.dynamo_info["Updated"], "%Y-%m-%dT%H:%M:%S"))
    upgraded_time_pt = upgraded_time_utc.astimezone(pytz.timezone("US/Pacific"))

    role_name = f"PantherSupportRole-{region}"
    url_support_name = urllib.parse.quote(f"{company_name} Support")

    expected_attrs = {
        "Account_Info_Auto_Updated":
        True,
        # Ignoring AWS_Organization
        # Ignoring Backend
        "Deploy_Group":
        standardize_deploy_group(account_info.deploy_yml_info.get("DeploymentGroup")),
        # Ignoring Deploy Type
        "Email":
        f"panther-hosted+{account_info.fairytale_name}@panther.io",
        # Ignoring Legacy_Stacks
        "Account_Name":
        create_rtf_value(
            text=company_name,
            url=f"https://{account_info.dynamo_info['GithubCloudFormationParameters']['CustomDomain']}/sign-in"),
        # Ignoring PoC
        "Region":
        region,
        # Ignoring Service_Type
        # Notion doesn't keep the seconds field, so zero it out in the Dynamo value
        "Upgraded":
        create_date_time_value(upgraded_time_pt.replace(second=0)),
        "Version":
        get_version_number(account_info.dynamo_info["PantherTemplateURL"], account_info.notion_info.Version),
    }

    if aws_account_id != IGNORE_FIELD:
        expected_attrs["AWS_Account_ID"] = aws_account_id
        expected_attrs["Support_Role"] = create_rtf_value(
            text=role_name,
            url=(f"https://{region}.signin.aws.amazon.com/switchrole?roleName={role_name}&account={aws_account_id}&"
                 f"displayName={url_support_name}"))
    return expected_attrs


def needs_update(attr, notion_val, update_val, notion_page):
    if update_val is IGNORE_FIELD:
        return False

    if (attr == "Upgraded") and str(notion_val) and str(update_val):
        return str(notion_val) != str(update_val)
    if attr in ("Account_Name", "Support_Role"):
        page_prop = attr.replace("_", " ")
        return not are_rtf_values_equal(notion_page.properties[page_prop].rich_text, update_val.rich_text)

    return notion_val != update_val


def set_updated_field_to_false_for_ignored_accounts(all_accounts):
    for fairytale_name, notion_info in all_accounts.notion_accounts.items():
        if fairytale_name in all_accounts.uncommon_fairytale_names:
            if notion_info.Account_Info_Auto_Updated:
                notion_info.Account_Info_Auto_Updated = False
                notion_info.commit()


def main(params):
    hosted_deploy_dir = (params["hosted_deploy_dir"]
                         if "hosted_deploy_dir" in params else git_clone(repo="hosted-deployments", github_setup=True))
    staging_deploy_dir = (params["staging_deploy_dir"] if "staging_deploy_dir" in params else git_clone(
        repo="staging-deployments", github_setup=True))
    all_accounts = AllCustomerAccountsInfo(hosted_deploy_dir=hosted_deploy_dir, staging_deploy_dir=staging_deploy_dir)

    print(f"Accounts that will be skipped due to not existing in Notion or hosted/staging deployments:\n"
          f"{all_accounts.uncommon_fairytale_names}")
    set_updated_field_to_false_for_ignored_accounts(all_accounts=all_accounts)

    for account_info in all_accounts:
        expected_attrs = get_expected_customer_attributes(account_info)
        for attr in expected_attrs:
            current_val, = getattr(account_info.notion_info, attr),
            update_val = expected_attrs[attr]
            if needs_update(attr, current_val, update_val, account_info.notion_info.page):
                print(f"{attr} will be updated for {account_info.fairytale_name}:\n{current_val} -> {update_val}\n\n")
                # Attribute changes to Notional automatically update the page as of version 0.1.0:
                # https://github.com/jheddings/notional/commit/d3725b1bd7b283e7269645fb59a178440e1a4fd1
                # Notion pages no longer have a commit function
                setattr(account_info.notion_info, attr, update_val)
