from dataclasses import dataclass

from v2.task_models.airplane_task import AirplaneTask
from v2.pyshared.sf_client import get_account_admin_client, exec_sql_cmds, parse_sql_results


@dataclass
class AirplaneParams:
    fairytale_name: str


class AccountLocatorRetriever(AirplaneTask):

    def run(self, params):
        ap_params = AirplaneParams(**params)
        data = self.get_sf_results(ap_params.fairytale_name)

        if len(data) < 1:
            raise RuntimeError(f"The Snowflake account could not be found for {ap_params.fairytale_name}")
        if len(data) > 1:
            raise RuntimeError(f"More than 1 Snowflake account found for {ap_params.fairytale_name}")
        return {"account_locator": data[0]["account_locator"]}

    @staticmethod
    def get_sf_results(fairytale_name):
        sf_client = get_account_admin_client()
        result = exec_sql_cmds(
            client=sf_client,
            sql_cmds=["USE ROLE ORGADMIN;", f"SHOW ORGANIZATION ACCOUNTS like '%{fairytale_name.replace('-', '_')}%';"])
        return parse_sql_results(result=result)


def main(params):
    return AccountLocatorRetriever().run(params)
