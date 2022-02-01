import os
import yaml

from pyshared.aws_creds import get_assumed_role_creds
from pyshared.dynamo_db import DynamoDbSearch
from pyshared.dynamo_db_tables import HOSTED_DEPLOYMENTS_METADATA, STAGING_DEPLOYMENTS_METADATA
from notion.auth import notion_session
from notion.databases import AccountsDatabase

DYNAMO_RO_ROLE_ARN = os.environ.get("DYNAMO_RO_ROLE_ARN")
ROOT_DYNAMO_RO_ROLE_ARN = os.environ.get("ROOT_DYNAMO_RO_ROLE_ARN")


class CustomerAccountInfo:
    def __init__(self, fairytale_name: str, deploy_yml_info: dict, dynamo_info: dict, notion_info: AccountsDatabase):
        self.deploy_yml_info = deploy_yml_info
        self.dynamo_info = dynamo_info
        self.fairytale_name = fairytale_name
        self.notion_info = notion_info


class AllCustomerAccountsInfo:
    def __init__(self, hosted_deploy_dir, staging_deploy_dir):
        self.dynamo_accounts = self.get_dynamo_results()
        self.notion_accounts = self.get_notion_results()
        self.deploy_yml_accounts = self.get_deploy_yml_accounts(hosted_deploy_dir)
        self.deploy_yml_accounts = {**self.deploy_yml_accounts, **self.get_deploy_yml_accounts(staging_deploy_dir)}
        self.common_fairytale_names, self.uncommon_fairytale_names = self._get_common_and_uncommon_fairytale_names()

    def __iter__(self):
        """Iterate over all accounts that are common for all sources of account information."""
        for fairytale_name in self.common_fairytale_names:
            yield self.get_account_info(fairytale_name=fairytale_name)

    @staticmethod
    def get_dynamo_results() -> dict[str, dict]:
        results = {}

        for table_name, arn in ((HOSTED_DEPLOYMENTS_METADATA, DYNAMO_RO_ROLE_ARN),
                                (STAGING_DEPLOYMENTS_METADATA, ROOT_DYNAMO_RO_ROLE_ARN),):
            db_search = DynamoDbSearch(
                table_name=table_name, assumed_role_creds=get_assumed_role_creds(arn=arn)
            )
            results = {**results, **db_search.scan_and_organize_result(scan_result_keys=("CustomerId",))}

        return results

    @staticmethod
    def get_notion_results() -> dict[str, AccountsDatabase]:
        return {account.Fairytale_Name: account
                for account in notion_session.databases.query(AccountsDatabase).execute()}

    @staticmethod
    def get_deploy_yml_accounts(hosted_deploy_dir) -> dict[str, dict]:
        deploy_yml_accounts = {}

        targets_dir = os.path.join(hosted_deploy_dir, "deployment-metadata", "deployment-targets")
        for customer_file in os.listdir(targets_dir):
            if not customer_file.endswith(".yml"):
                continue
            fairytale_name = os.path.splitext(customer_file)[0]
            with open(os.path.join(targets_dir, customer_file), "r") as file_handler:
                deploy_yml_accounts[fairytale_name] = yaml.safe_load(file_handler)

        return deploy_yml_accounts

    def _get_common_and_uncommon_fairytale_names(self) -> set[str]:
        deploy = set(self.deploy_yml_accounts)
        dynamo = set(self.dynamo_accounts)
        notion = set(self.notion_accounts)

        common = deploy.intersection(dynamo.intersection(notion))
        uncommon = deploy.difference(common) | dynamo.difference(common) | notion.difference(common)
        return common, uncommon

    def get_account_info(self, fairytale_name) -> CustomerAccountInfo:
        return CustomerAccountInfo(
            fairytale_name=fairytale_name,
            deploy_yml_info=self.deploy_yml_accounts[fairytale_name],
            dynamo_info=self.dynamo_accounts[fairytale_name],
            notion_info=self.notion_accounts[fairytale_name]
        )
