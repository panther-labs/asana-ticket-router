from pyshared.customer_info_retriever import AllCustomerAccountsInfo


def _get_unfinished_airplane_creation_accounts():
    notion_entries = AllCustomerAccountsInfo.get_notion_results()
    return [
        fairytale_name for fairytale_name, notion_info in notion_entries.items()
        if not notion_info.Airplane_Creation_Completed
    ]


def main(params):
    return {"unfinished_airplane": _get_unfinished_airplane_creation_accounts()}
