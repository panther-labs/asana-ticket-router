from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from operations.deprovisions import DEPROV_TZ
from pyshared.airplane_utils import AirplaneTask
from pyshared.deprov_info import DeprovInfo


@dataclass
class AirplaneParams:
    fairytale_name: str
    hours_before_dns_removal: int
    hours_before_teardown: int
    org_name: str
    aws_account_id: str
    company_display_name: str
    domain: str
    region: str


class DeprovInfoGenerator(AirplaneTask):

    def main(self, params):
        ap_params = AirplaneParams(**params)
        now = datetime.now(DEPROV_TZ)
        dns_removal_time = now + timedelta(hours=ap_params.hours_before_dns_removal)
        teardown_time = now + timedelta(hours=ap_params.hours_before_teardown)
        deprov_info = DeprovInfo(dns_removal_time=str(dns_removal_time),
                                 teardown_time=str(teardown_time),
                                 aws_account_id=ap_params.aws_account_id,
                                 organization=ap_params.org_name,
                                 region=ap_params.region)

        dns_removal_time_readable, teardown_time_readable = self._get_human_readable_times(
            dns_removal_time, teardown_time)
        slack_msg = f"""Customer {ap_params.fairytale_name} has been marked to be deleted.

Please make sure this is intentional.

AWS Account ID: {ap_params.aws_account_id}
Company Display Name: {ap_params.company_display_name}
Domain: {ap_params.domain}
Fairytale name: {ap_params.fairytale_name}

Time when DNS will be removed (no more access to their instance via the browser): {dns_removal_time_readable}
Time when the instance will be torn down (an unrecoverable operation): {teardown_time_readable}

Was this a mistake? Do the following:
Notify the deployment team to remove deletion info from the deployment file for {ap_params.fairytale_name}
        """
        self.send_slack_message(channel_name="#eng-deployment-notifications", message=slack_msg)
        return asdict(deprov_info)

    @staticmethod
    def _get_human_readable_times(dns_removal_time, teardown_time):
        time_format = "%m/%d/%Y, %H:%M:%S %Z"
        return dns_removal_time.strftime(time_format), teardown_time.strftime(time_format)


def main(params):
    return DeprovInfoGenerator().main(params)
