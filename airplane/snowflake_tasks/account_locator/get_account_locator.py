from dataclasses import dataclass

from v2.task_models.airplane_task import AirplaneTask
from v2.pyshared.sf_client import get_account_admin_client, exec_sql_cmds, parse_sql_results


@dataclass
class AirplaneParams:
    fairytale_name: str
    send_slack_msg: bool


class AccountLocatorRetriever(AirplaneTask):

    def run(self, params):
        ap_params = AirplaneParams(**params)
        account_names_and_locators = [(sql_row["account_name"], sql_row["account_locator"])
                                      for sql_row in self.get_sf_results(ap_params.fairytale_name)]
        if ap_params.send_slack_msg:
            self.send_slack_notification_to_deployment_team(fairytale_name=ap_params.fairytale_name,
                                                            account_names_and_locators=account_names_and_locators)
        return {"account_names_and_locators": account_names_and_locators}

    @staticmethod
    def get_sf_results(fairytale_name):
        sf_client = get_account_admin_client()
        result = exec_sql_cmds(
            client=sf_client,
            sql_cmds=["USE ROLE ORGADMIN;", f"SHOW ORGANIZATION ACCOUNTS like '%{fairytale_name.replace('-', '_')}%';"])
        return parse_sql_results(result=result)

    def send_slack_notification_to_deployment_team(self, fairytale_name, account_names_and_locators):
        if not account_names_and_locators:
            msg = (f"For deprovisioning, no Snowflake locators were found for customer {fairytale_name}. "
                   "Confirm we don't manage their Snowflake account.")
        elif len(account_names_and_locators) == 1:
            account_name, locator = account_names_and_locators[0]
            url = "https://www.notion.so/pantherlabs/Deleting-Snowflake-Account-1db19d43b84541c79558244ab7760e93"
            msg = (f"For deprovisioning, confirm we manage {fairytale_name}'s Snowflake account. If so, open a support "
                   f"case to teardown that account (see {url}). Account name: {account_name}, Locator {locator}")
        else:
            msg = (f"For deprovisioning, multiple locators were found for {fairytale_name}."
                   "Does anything in Snowflake need to be requested for deletion?")

        self.send_slack_message(channel_name="#triage-deployment", message=msg)


def main(params):
    return AccountLocatorRetriever().run(params)
