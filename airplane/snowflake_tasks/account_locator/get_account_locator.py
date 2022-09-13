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
        locators = [sql_row["account_locator"] for sql_row in self.get_sf_results(ap_params.fairytale_name)]
        if ap_params.send_slack_msg:
            self.send_slack_notification_to_deployment_team(fairytale_name=ap_params.fairytale_name, locators=locators)
        return {"account_locators": locators}

    @staticmethod
    def get_sf_results(fairytale_name):
        sf_client = get_account_admin_client()
        result = exec_sql_cmds(
            client=sf_client,
            sql_cmds=["USE ROLE ORGADMIN;", f"SHOW ORGANIZATION ACCOUNTS like '%{fairytale_name.replace('-', '_')}%';"])
        return parse_sql_results(result=result)

    def send_slack_notification_to_deployment_team(self, fairytale_name, locators):
        if not locators:
            msg = f"No locators were found. Confirm we don't manage snowflake for customer {fairytale_name}"
        elif len(locators) == 1:
            url = "https://www.notion.so/pantherlabs/Deleting-Snowflake-Account-1db19d43b84541c79558244ab7760e93"
            msg = (f"Locator {locators[0]} found for {fairytale_name}. Confirm we manage their snowflake account, "
                   f"and if so, follow {url} to teardown that Snowflake account.")
        else:
            msg = (f"Multiple locators found for {fairytale_name}."
                   "Does anything in Snowflake need to be requested for deletion?")

        self.send_slack_message(channel_name="#triage-deployment", message=msg)


def main(params):
    return AccountLocatorRetriever().run(params)
