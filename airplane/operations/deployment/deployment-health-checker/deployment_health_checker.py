from pyshared.airplane_utils import AirplaneTask
from pyshared.customer_info_retriever import AllCustomerAccountsInfo


class DeploymentHealthChecker(AirplaneTask):

    def __init__(self):
        self.notion_entries = AllCustomerAccountsInfo.get_notion_results()

    def _get_unfinished_airplane_creation_accounts(self):
        return [
            fairytale_name for fairytale_name, notion_info in self.notion_entries.items()
            if (notion_info.Airplane_Creation_Link and not notion_info.Airplane_Creation_Completed)
        ]

    def _get_mismatched_panther_versions(self):

        def versions_do_not_match(notion_info):
            return notion_info.Actual_Version and notion_info.Expected_Version and (notion_info.Actual_Version !=
                                                                                    notion_info.Expected_Version)

        return [{
            fairytale_name: {
                "Expected Version": notion_info.Expected_Version,
                "Actual Version": notion_info.Actual_Version
            }
        } for fairytale_name, notion_info in self.notion_entries.items() if versions_do_not_match(notion_info)]

    def main(self):
        return {
            "unfinished_airplane": self._get_unfinished_airplane_creation_accounts(),
            "mismatched_panther_versions": self._get_mismatched_panther_versions(),
            "runbook_url": self.get_runbook_run_url(),
        }


def main(_):
    return DeploymentHealthChecker().main()
