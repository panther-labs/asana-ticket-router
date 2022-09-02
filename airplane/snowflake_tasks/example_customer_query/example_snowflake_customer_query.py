from dataclasses import dataclass

from v2.task_models.airplane_task import AirplaneTask
from v2.pyshared.sf_client import get_customer_client, exec_sql_cmds, parse_sql_results


@dataclass
class AirplaneParams:
    fairytale_name: str


class ExampleSnowflakeCustomerQuery(AirplaneTask):

    def run(self, params):
        ap_params = AirplaneParams(**params)
        sf_client = get_customer_client(ap_params.fairytale_name)
        result = exec_sql_cmds(client=sf_client, sql_cmds=["show databases;"])
        return self.convert_all_columns_strs(parse_sql_results(result=result))

    @staticmethod
    def convert_all_columns_strs(data):
        parsed = []
        for row in data:
            parsed.append({key: str(val) for key, val in row.items()})
        return parsed


def main(params):
    return ExampleSnowflakeCustomerQuery().run(params)
