import airplane

from snowflake_tasks import ENV_VARS
from v2.task_models.airplane_task import AirplaneTask
from v2.pyshared.sf_client import get_customer_client, exec_sql_cmds, parse_sql_results


class ExampleSnowflakeCustomerQuery(AirplaneTask):

    def run(self, fairytale_name: str):
        sf_client = get_customer_client(fairytale_name)
        result = exec_sql_cmds(client=sf_client, sql_cmds=["show databases;"])
        return self.convert_all_columns_strs(parse_sql_results(result=result))

    @staticmethod
    def convert_all_columns_strs(data):
        parsed = []
        for row in data:
            parsed.append({key: str(val) for key, val in row.items()})
        return parsed


@airplane.task(name=f"Example Snowflake Customer Query", env_vars=ENV_VARS)
def example_snowflake_customer_query(fairytale_name: str):
    return ExampleSnowflakeCustomerQuery().run(fairytale_name)
