# Linked to https://app.airplane.dev/t/move_notion_panther_deploy_to_deprovisioned [do not edit this line]
from pyshared.notion_auth import NotionSession
from pyshared.notion_databases import get_accounts_database


def move_notion_deploy_entry_to_deprovision(fairytale_name, test_run):
    account = next((account for account in NotionSession.session.databases.query(get_accounts_database()).execute()
                    if account.Fairytale_Name == fairytale_name), None)
    if account:
        if test_run:
            print(f"Found {fairytale_name} account, but not doing anything since this is a test run")
        else:
            account.Service_Type = "Deprovision"
            account.commit()
            print(f"Moved account {fairytale_name} to the Deprovision group")
    else:
        print(f"Did not find account {fairytale_name}, doing nothing")


def main(params):
    move_notion_deploy_entry_to_deprovision(fairytale_name=params["fairytale_name"],
                                            test_run=params["airplane_test_run"])
