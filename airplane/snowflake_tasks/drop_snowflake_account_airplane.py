import airplane

from snowflake_tasks import ENV_VARS
from v2.task_models.airplane_task import AirplaneTask
from v2.pyshared.sf_client import get_account_admin_client, get_customer_sf_name, exec_sql_cmds, parse_sql_results


class SnowflakeAccountTeardown(AirplaneTask):

    def run(self, fairytale_name: str, grace_period_days=7):
        result = exec_sql_cmds(
            client=get_account_admin_client(),
            sql_cmds=[
                "USE ROLE ORGADMIN;",
                (f"DROP ORGANIZATION ACCOUNT {get_customer_sf_name(fairytale_name)} GRACE_PERIOD_IN_DAYS = "
                 f"{grace_period_days};")
            ])
        return parse_sql_results(result=result)


@airplane.task(name="Drop Snowflake Account", env_vars=ENV_VARS)
def drop_snowflake_account(fairytale_name: str, grace_period_days: int = 7):
    return SnowflakeAccountTeardown(requires_parent_execution=True).run(fairytale_name, grace_period_days)
