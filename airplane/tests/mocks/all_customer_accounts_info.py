from pyshared.customer_info_retriever import AllCustomerAccountsInfo

from tests.mocks.deployment_metadata_table import get_metadata_table_ddb_cfg
from tests.mocks.notion_databases import MockAccountsDatabase


class MockAllCustomerAccountsInfo(AllCustomerAccountsInfo):

    def __init__(self, *_, **__):
        self.common_fairytale_names = []
        self.dynamo_accounts = {}
        self.notion_accounts = {}
        self.notion_duplicates = []

    def create_fake_customer(self, fairytale_name, dynamo=None, notion=None):
        self.common_fairytale_names.append(fairytale_name)
        self.dynamo_accounts[fairytale_name] = dynamo if dynamo else get_metadata_table_ddb_cfg()
        self.notion_accounts[fairytale_name] = notion if notion else MockAccountsDatabase()

    def get_notion_results(self, *_, **__):
        return self.notion_accounts

    def get_dynamo_results(self, *_, **__):
        return self.dynamo_accounts

    def get_notion_duplicates(self):
        return self.notion_duplicates
