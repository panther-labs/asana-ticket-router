import datetime
import pytz
import urllib.parse
from typing import Optional

from notional import types as notional_types
from notional.text import FullColor

from pyshared.customer_info_retriever import AllCustomerAccountsInfo
from pyshared.deployments_file import DeploymentsRepo
from pyshared.git_ops import AirplaneMultiCloneGitTask
from pyshared.notion_auth import NotionSession
from pyshared.notion_databases import are_text_objects_equal, create_date_time_value, create_rtf_value, \
    get_accounts_database, get_display_rtf_value


class UpdateDeploymentRecords(AirplaneMultiCloneGitTask):
    EMPTY_FIELD = ""
    IGNORE_FIELD = None
    WARNING_COLOR = "\033[93m"

    def __init__(self):
        super().__init__(git_repos=(DeploymentsRepo.HOSTED, DeploymentsRepo.STAGING))
        self.all_accounts: Optional[AllCustomerAccountsInfo] = None

    def main(self, params):
        self.add_missing_notion_entries()
        self.remove_duplicate_notion_entries()
        # Only get all the accounts after missing accounts have been added
        self.all_accounts = AllCustomerAccountsInfo(hosted_deploy_dir=self.git_dirs[DeploymentsRepo.HOSTED],
                                                    staging_deploy_dir=self.git_dirs[DeploymentsRepo.STAGING],
                                                    test_roles=self.test_roles)
        self.set_ignored_notion_entries()
        self.update_notion_entries()

    def set_ignored_notion_entries(self):
        print(f"Accounts that will be skipped due to not existing in Notion or hosted/staging deployments:\n"
              f"{self.all_accounts.missing_notion_updates}")

        for fairytale_name, notion_info in self.all_accounts.notion_accounts.items():
            if fairytale_name in self.all_accounts.uncommon_fairytale_names:
                if notion_info.Account_Info_Auto_Updated:
                    print(f"Set {fairytale_name} to not be auto updated")
                    if not self.is_test_run():
                        notion_info.Account_Info_Auto_Updated = False

    def add_missing_notion_entries(self):
        """Useful if anyone accidentally deletes a row from the Notion DB - adds any accounts in GH not found in
        Notion. This only adds the fairytale name and lets the rest of this task add the rest."""
        deploy = {
            **AllCustomerAccountsInfo.get_deploy_yml_accounts(self.git_dirs[DeploymentsRepo.HOSTED]),
            **AllCustomerAccountsInfo.get_deploy_yml_accounts(self.git_dirs[DeploymentsRepo.STAGING])
        }
        notion = AllCustomerAccountsInfo.get_notion_results()
        missing_names = set(deploy).difference(set(notion))
        notion_db = get_accounts_database()

        for fairytale_name in missing_names:
            print(f"Adding missing account, '{fairytale_name}', to Notion")
            if not self.is_test_run():
                notion_db.create(Fairytale_Name=fairytale_name)

    @staticmethod
    def remove_duplicate_notion_entries():
        """Search for duplicate accounts not managed by this script and remove them"""
        all_accounts = AllCustomerAccountsInfo.get_notion_results_list()
        duplicate_accounts = {}
        for account in all_accounts:
            if account.Fairytale_Name in duplicate_accounts:
                remove_account = None
                if not account.Account_Info_Auto_Updated:
                    remove_account = account
                elif not duplicate_accounts[account.Fairytale_Name].Account_Info_Auto_Updated:
                    remove_account = duplicate_accounts[account.Fairytale_Name]
                    duplicate_accounts[account.Fairytale_Name] = account
                if remove_account:
                    notion_page = UpdateDeploymentRecords._get_notion_page(remove_account)
                    NotionSession().session.pages.delete(notion_page)
            else:
                duplicate_accounts[account.Fairytale_Name] = account

    def update_notion_entries(self):
        for account_info in self.all_accounts:
            expected_attrs = self.get_expected_customer_attributes(account_info)
            for attr in expected_attrs:
                current_val = self.get_notion_value(attr=attr, account_info=account_info)
                update_val = expected_attrs[attr]
                if self.needs_update(attr, current_val, update_val):
                    print(f"{attr} will be updated for {account_info.fairytale_name}:\n" +
                          f"{self.get_display_value(current_val)} -> {self.get_display_value(update_val)}\n\n")
                    if not self.is_test_run():
                        setattr(account_info.notion_info, attr, update_val)

    @staticmethod
    def needs_update(attr, notion_val, update_val):
        if update_val is UpdateDeploymentRecords.IGNORE_FIELD:
            return False

        if (attr == "Upgraded") and str(notion_val) and str(update_val):
            return str(notion_val) != str(update_val)

        if isinstance(notion_val, notional_types.TextObject):
            return not are_text_objects_equal(notion_val, update_val.rich_text[0])

        return notion_val != update_val

    @staticmethod
    def standardize_deploy_group(deploy_group: str) -> str:
        if deploy_group is None:
            return deploy_group

        return {
            "cpaas": "CPaaS",
            "hold": "hold",
            "internal": "Internal"
        }.get(deploy_group.lower(), deploy_group.upper())

    @staticmethod
    def get_company_name(account_info):
        # For special cases, where the display name in Notion doesn't match what is in dynamo - we can override it by
        # filling in the Notes section of the Notion table entry
        notes = str(account_info.notion_info.Notes)
        name_key = "Name: "
        if name_key in notes:
            after_name_index = notes.index(name_key) + len(name_key)

            notes = notes[after_name_index:]
            return notes.split(",")[0]
        return account_info.dynamo_info["GithubCloudFormationParameters"]["CompanyDisplayName"]

    @staticmethod
    def get_notion_value(attr, account_info):
        if attr in ("Account_Name", "Support_Role", "Expected_Version", "Actual_Version"):
            page_prop = attr.replace("_", " ")
            text_object = UpdateDeploymentRecords._get_notion_page(
                account_info.notion_info).properties[page_prop].rich_text
            if text_object:
                return text_object[0] if isinstance(text_object, list) else text_object
            else:
                return create_rtf_value(text="", url="")
        return getattr(account_info.notion_info, attr)

    @staticmethod
    def get_display_value(value):
        if isinstance(value, notional_types.RichText):
            return get_display_rtf_value(value)
        return value

    @staticmethod
    def get_org(account_info):
        if account_info.github_repo == DeploymentsRepo.STAGING:
            return "panther-root"

        if account_info.dynamo_info["DeploymentType"].lower() in ["cpaas", "self hosted"]:
            return "customer"

        return "panther-hosted-root"

    @staticmethod
    def get_expected_customer_attributes(account_info):
        aws_account_id = account_info.dynamo_info.get("AWSConfiguration", {}).get("AccountId",
                                                                                  UpdateDeploymentRecords.IGNORE_FIELD)
        company_name = UpdateDeploymentRecords.get_company_name(account_info)
        region = account_info.dynamo_info["GithubConfiguration"]["CustomerRegion"]
        upgraded_time_utc = pytz.timezone("UTC").localize(
            datetime.datetime.strptime(account_info.dynamo_info["Updated"], "%Y-%m-%dT%H:%M:%S"))
        upgraded_time_pt = upgraded_time_utc.astimezone(pytz.timezone("US/Pacific"))

        role_name = f"PantherSupportRole-{region}"
        url_support_name = urllib.parse.quote(f"{company_name} Support")
        email_domain = account_info.dynamo_info["GithubConfiguration"]["BaseRootEmail"].split("@")[1]

        expected_attrs = {
            "Account_Info_Auto_Updated":
            True,
            "Account_Name":
            create_rtf_value(
                text=company_name,
                url=f"https://{account_info.dynamo_info['GithubCloudFormationParameters']['CustomDomain']}/sign-in"),
            "AWS_Organization":
            UpdateDeploymentRecords.get_org(account_info),
            # Ignoring Backend
            "Deploy_Group":
            UpdateDeploymentRecords.standardize_deploy_group(
                account_info.dynamo_info["GithubConfiguration"].get("DeploymentGroup")),
            # Ignoring Deploy Type
            "Email":
            f"panther-hosted+{account_info.fairytale_name}@{email_domain}",
            # Ignoring Legacy_Stacks
            # Ignoring PoC
            "Region":
            region,
            # Ignoring Service_Type
            # Notion doesn't keep the seconds field, so zero it out in the Dynamo value
            "Upgraded":
            create_date_time_value(upgraded_time_pt.replace(second=0)),
        }

        if aws_account_id != UpdateDeploymentRecords.IGNORE_FIELD:
            expected_attrs["AWS_Account_ID"] = aws_account_id
            expected_attrs["Support_Role"] = create_rtf_value(
                text=role_name,
                url=(f"https://{region}.signin.aws.amazon.com/switchrole?roleName={role_name}&account={aws_account_id}&"
                     f"displayName={url_support_name}"))

        actual_version = account_info.dynamo_info.get("ActualVersion", "").replace("v", "")
        expected_version = account_info.dynamo_info.get("ExpectedVersion", "").replace("v", "")
        version_color = FullColor.GREEN_BACKGROUND
        if (actual_version and expected_version) and actual_version != expected_version:
            version_color = FullColor.RED_BACKGROUND

        if actual_version:
            expected_attrs["Actual_Version"] = create_rtf_value(text=actual_version, color=version_color)
        if expected_version:
            expected_attrs["Expected_Version"] = create_rtf_value(text=expected_version, color=version_color)
        return expected_attrs

    @staticmethod
    def _get_notion_page(notion_info):
        # This private member used to be public, and to my knowledge, is the only way to get the actual
        # contents of a rich text field rather than just the text (or delete the page).
        # noinspection PyProtectedMember
        return notion_info._notional__page


def main(_):
    UpdateDeploymentRecords().main({})
