import os
import yaml

from pyshared.aws_consts import get_aws_const
from pyshared.dynamo_db import DynamoDbSearch
from pyshared.notion_auth import notion_session
from pyshared.notion_databases import AccountsDatabase

HOSTED_DYNAMO_RO_ROLE_ARN = get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_ARN")
HOSTED_DEPLOYMENTS_METADATA = get_aws_const(const_name="HOSTED_DEPLOYMENTS_METADATA")
ROOT_DYNAMO_RO_ROLE_ARN = get_aws_const(const_name="ROOT_DYNAMO_RO_ROLE_ARN")
STAGING_DEPLOYMENTS_METADATA = get_aws_const(const_name="STAGING_DEPLOYMENTS_METADATA")


class CustomerAccountInfo:

    def __init__(self, fairytale_name: str, deploy_yml_info: dict, dynamo_info: dict, notion_info: AccountsDatabase):
        self.deploy_yml_info = deploy_yml_info
        self.dynamo_info = dynamo_info
        self.fairytale_name = fairytale_name
        self.notion_info = notion_info


class AllCustomerAccountsInfo:

    def __init__(self, hosted_deploy_dir=None, staging_deploy_dir=None):
        self.dynamo_accounts = self.get_dynamo_results(get_hosted=(hosted_deploy_dir is not None),
                                                       get_staging=(staging_deploy_dir is not None))
        self.notion_accounts = self.get_notion_results()
        self.deploy_yml_accounts = {}
        if hosted_deploy_dir is not None:
            self.deploy_yml_accounts = {**self.deploy_yml_accounts, **self.get_deploy_yml_accounts(hosted_deploy_dir)}
        if staging_deploy_dir is not None:
            self.deploy_yml_accounts = {**self.deploy_yml_accounts, **self.get_deploy_yml_accounts(staging_deploy_dir)}
        self.common_fairytale_names, self.uncommon_fairytale_names = self._get_common_and_uncommon_fairytale_names()

    def __iter__(self):
        """Iterate over all accounts that are common for all sources of account information."""
        for fairytale_name in self.common_fairytale_names:
            yield self.get_account_info(fairytale_name=fairytale_name)

    @staticmethod
    def get_dynamo_results(get_hosted, get_staging) -> dict[str, dict]:
        results = {}

        tables_and_arns = []
        if get_hosted:
            tables_and_arns.append((HOSTED_DEPLOYMENTS_METADATA, HOSTED_DYNAMO_RO_ROLE_ARN))
        if get_staging:
            tables_and_arns.append((STAGING_DEPLOYMENTS_METADATA, ROOT_DYNAMO_RO_ROLE_ARN))

        for table_name, arn in tables_and_arns:
            db_search = DynamoDbSearch(table_name=table_name, arn=arn)
            results = {**results, **db_search.scan_and_organize_result(scan_result_keys=("CustomerId", ))}

        return results

    @staticmethod
    def get_notion_results() -> dict[str, AccountsDatabase]:
        return {
            account.Fairytale_Name: account
            for account in notion_session.databases.query(AccountsDatabase).execute() if account.Fairytale_Name
        }

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
        return CustomerAccountInfo(fairytale_name=fairytale_name,
                                   deploy_yml_info=self.deploy_yml_accounts[fairytale_name],
                                   dynamo_info=self.dynamo_accounts[fairytale_name],
                                   notion_info=self.notion_accounts[fairytale_name])


def retrieve_notion_account(fairytale_name):
    notion_entries = AllCustomerAccountsInfo.get_notion_results()

    try:
        return notion_entries[fairytale_name]
    except KeyError:
        raise ValueError(f"Panther Deploy in Notion with fairytale name '{fairytale_name}' does not exist")