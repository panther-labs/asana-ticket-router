from dataclasses import dataclass

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from v2.task_models.airplane_task import AirplaneTask


@dataclass
class AirplaneParams:
    aws_account_id: str
    organization: str
    region: str


class PantherTeardown(AirplaneTask):

    @staticmethod
    def _get_client(aws_account_id):
        return get_credentialed_client(service_name="codebuild",
                                       arns=get_aws_const("CODEBUILD_LAUNCH_RETRIEVE_ROLE_ARN"),
                                       desc=f"launch_teardown_codebuild_{aws_account_id}",
                                       region="us-west-2")

    @staticmethod
    def _get_override_env_vars(region, aws_account_id):
        name_vals = {"PANTHER_REGION": region, "ROLE_ARN": aws_account_id}
        return [{"name": name, "value": value, "type": "PLAINTEXT"} for name, value in name_vals.items()]

    def run(self, params):
        ap_params = AirplaneParams(**params)
        if ap_params.organization != "hosted":
            raise NotImplementedError("Only hosted-root org works at this time")
        codebuild_client = self._get_client(ap_params.aws_account_id)
        rsp = codebuild_client.start_build(projectName="teardown-deployment",
                                           environmentVariablesOverride=self._get_override_env_vars(
                                               ap_params.region, ap_params.aws_account_id))
        return {"build_arn": rsp["build"]["arn"]}


def main(params):
    return PantherTeardown().run(params)
