from dataclasses import dataclass

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from v2.task_models.airplane_task import AirplaneTask


@dataclass
class AirplaneParams:
    build_id: str
    organization: str


class PantherTeardownRetriever(AirplaneTask):

    @staticmethod
    def _get_client():
        return get_credentialed_client(service_name="codebuild",
                                       arns=get_aws_const("CODEBUILD_LAUNCH_RETRIEVE_ROLE_ARN"),
                                       desc=f"retrieve_teardown_codebuild",
                                       region="us-west-2")

    def run(self, params):
        ap_params = AirplaneParams(**params)
        if ap_params.organization != "hosted":
            raise NotImplementedError("Only hosted-root org works at this time")
        codebuild_client = self._get_client()
        rsp = codebuild_client.batch_get_builds(ids=[ap_params.build_id])
        return {"build_status": rsp["builds"][0]["buildStatus"]}


def main(params):
    return PantherTeardownRetriever().run(params)
