import datetime
import pytz

from dataclasses import dataclass

from pyshared.airplane_utils import AirplaneTask
from pyshared.notion_databases import create_rtf_value, get_accounts_database


@dataclass
class AirplaneParams:
    fairytale_name: str
    aws_account_id: str
    version: str
    region: str
    backend: str
    service_type: str
    poc: bool
    support_role: str
    email: str
    account_name: str
    airplane_test_run: bool


class NewPantherDeployNotionRecord(AirplaneTask):

    def __init__(self, params):
        self.unparsed_params = params
        self.ap_params = AirplaneParams(**params)

    def main(self):
        get_accounts_database().create(
            Account_Name=self.ap_params.account_name,
            Airplane_Creation_Link=self.get_runbook_run_url(),
            AWS_Account_ID=self.ap_params.aws_account_id,
            AWS_Organization="panther-hosted-root",
            Backend={"Managed": "Managed SF"}.get(self.ap_params.backend, self.ap_params.backend),
            Deploy_Group="L",
            Email=self.ap_params.email,
            Fairytale_Name=self.ap_params.fairytale_name,
            PoC=self.ap_params.poc,
            Region=self.ap_params.region,
            Service_Type=self.ap_params.service_type if not self.ap_params.airplane_test_run else "Airplane Testing",
            Support_Role=create_rtf_value(
                text=self.ap_params.support_role,
                url=(f"https://{self.ap_params.region}.signin.aws.amazon.com/switchrole?"
                     f"roleName={self.ap_params.support_role}&account={self.ap_params.aws_account_id}&"
                     f"displayName={self.ap_params.account_name}%20Support")),
            Upgraded=datetime.datetime.now(pytz.timezone('US/Pacific')).date(),
            Version=self.ap_params.version,
        )

        return self.unparsed_params


def main(params):
    NewPantherDeployNotionRecord(params).main()
