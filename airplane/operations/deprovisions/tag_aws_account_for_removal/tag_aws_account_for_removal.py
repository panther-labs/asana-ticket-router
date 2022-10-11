from dataclasses import dataclass

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.airplane_utils import AirplaneTask


@dataclass
class AirplaneParams:
    aws_account_id: str
    organization: str


class AccountCloser(AirplaneTask):

    def main(self, params):
        ap_params = AirplaneParams(**params)
        client = get_credentialed_client(service_name="organizations",
                                         arns=get_aws_const(f"{ap_params.organization.upper()}_TAG_ACCOUNT_ROLE_ARN"),
                                         desc=f"tagging_aws_account_{ap_params.aws_account_id}")
        client.tag_resource(ResourceId=ap_params.aws_account_id, Tags=[{"Key": "ready_for_closing", "Value": "true"}])


def main(params):
    AccountCloser(requires_parent_execution=True).main(params)
