from dataclasses import dataclass

import airplane

from snowflake_tasks import ENV_VARS
from v2.task_models.airplane_task import AirplaneTask
from v2.pyshared.sf_client import get_account_admin_client, get_customer_sf_name, exec_sql_cmds, parse_sql_results


class AccountLocatorRetriever(AirplaneTask):

    def run(self, fairytale_name: str, send_slack_msg: bool = False):
        account_names_and_locators = [(sql_row["account_name"], sql_row["account_locator"])
                                      for sql_row in self.get_sf_results(fairytale_name)]
        return {"account_names_and_locators": account_names_and_locators}

    @staticmethod
    def get_sf_results(fairytale_name):
        sf_client = get_account_admin_client()
        result = exec_sql_cmds(client=sf_client,
                               sql_cmds=[
                                   "USE ROLE ORGADMIN;",
                                   f"SHOW ORGANIZATION ACCOUNTS like '%{get_customer_sf_name(fairytale_name)}%';"
                               ])
        return parse_sql_results(result=result)


@airplane.task(name=f"Get Snowflake Account Locator", env_vars=ENV_VARS)
def get_snowflake_account_locator(fairytale_name: str):
    """Get the account locator for a Snowflake account.

    Args:
      fairytale_name: Alias for customer
    """
    return AccountLocatorRetriever().run(fairytale_name)
