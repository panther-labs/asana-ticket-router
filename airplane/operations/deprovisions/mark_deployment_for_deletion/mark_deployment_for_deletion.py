from dataclasses import dataclass
from datetime import datetime, timedelta
import pytz

from pyshared.airplane_utils import AirplaneTask
from pyshared.deprov_info import DeprovInfo, DeprovInfoDeployFile
from pyshared.deployments_file import DeploymentsRepo, alter_deployment_file


@dataclass
class AirplaneParams:
    fairytale_name: str
    hours_before_dns_removal: int
    hours_before_teardown: int
    org_name: str
    aws_account_id: str
    company_display_name: str
    domain: str
    api_use_only: bool


class DeploymentDeletionMarker(AirplaneTask):

    @staticmethod
    def add_deprovisioning_tags(filepath,
                                dns_removal_hours,
                                teardown_removal_hours,
                                now=datetime.now(pytz.timezone("US/Pacific"))) -> DeprovInfo:
        deprov_info = DeprovInfo(dns_removal_time=now + timedelta(hours=dns_removal_hours),
                                 teardown_time=now + timedelta(hours=teardown_removal_hours))
        DeprovInfoDeployFile(filepath=filepath).write_deprov_info(deprov_info=deprov_info)
        return deprov_info

    def main(self, params):
        ap_params = AirplaneParams(**params)
        repo = DeploymentsRepo.HOSTED if ap_params.org_name == "hosted" else DeploymentsRepo.STAGING
        deprov_info, _ = alter_deployment_file(
            deployments_repo=repo,
            ap_params=params,
            alter_callable=lambda filepath: self.add_deprovisioning_tags(filepath, ap_params.hours_before_dns_removal,
                                                                         ap_params.hours_before_teardown),
            commit_title=f"Mark {params['fairytale_name']} for deprovisioning")

        dns_time, teardown_time = self._get_human_readable_times(deprov_info)
        slack_msg = f"""Customer {ap_params.fairytale_name} has been marked to be deleted.

Please make sure this is intentional.

AWS Account ID: {ap_params.aws_account_id}
Company Display Name: {ap_params.company_display_name}
Domain: {ap_params.domain}
Fairytale name: {ap_params.fairytale_name}

Time when DNS will be removed (no more access to their instance via the browser): {dns_time}
Time when the instance will be torn down (an unrecoverable operation): {teardown_time}

Was this a mistake? Do the following:
Notify the deployment team to remove deletion info from the deployment file for {ap_params.fairytale_name}
        """
        self.send_slack_message(channel_name="#eng-deployment-notifications", message=slack_msg)

    def _get_human_readable_times(self, deprov_info):
        time_format = "%m/%d/%Y, %H:%M:%S %Z"
        return deprov_info.dns_removal_time.strftime(time_format), deprov_info.teardown_time.strftime(time_format)


def main(params):
    DeploymentDeletionMarker(api_use_only=params["api_use_only"], requires_runbook=True).main(params)
