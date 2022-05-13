from pyshared.customer_info_retriever import AllCustomerAccountsInfo


def _get_unfinished_airplane_creation_accounts(notion_entries):
    return [
        fairytale_name for fairytale_name, notion_info in notion_entries.items()
        if (notion_info.Airplane_Creation_Link and not notion_info.Airplane_Creation_Completed)
    ]


def _get_mismatched_panther_versions(notion_entries):

    def versions_do_not_match(notion_info):
        return notion_info.Actual_Version and notion_info.Expected_Version and (notion_info.Actual_Version !=
                                                                                notion_info.Expected_Version)

    return [{
        fairytale_name: {
            "Expected Version": notion_info.Expected_Version,
            "Actual Version": notion_info.Actual_Version
        }
    } for fairytale_name, notion_info in notion_entries.items() if versions_do_not_match(notion_info)]


def main(params):
    notion_entries = AllCustomerAccountsInfo.get_notion_results()

    return {
        "unfinished_airplane": _get_unfinished_airplane_creation_accounts(notion_entries),
        "mismatched_panther_versions": _get_mismatched_panther_versions(notion_entries)
    }
