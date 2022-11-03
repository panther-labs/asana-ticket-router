# Testing:
# - Manually edit tests/v2/security/test_hosted_account_log_sources.py with desired params
# - Assume the hosted-security-onboarding-role AWS profile from aws-vault
# - pytest --manual-test tests/v2/security/test_hosted_account_log_sources.py
import json

import airplane

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from v2.consts.airplane_env import AirplaneEnv
from v2.task_models.airplane_task import AirplaneTask

ENV_VARS = [airplane.EnvVar(name="ECS_TASK_ROLE", value=get_aws_const("SECURITY_LOG_ONBOARDING_ECS_ROLE"))]
KOS_AWS_ACCOUNT_ID = "964675078129"
TASK_NAME = "hosted-account log-sources"


class HostedAccountLogSources(AirplaneTask):

    def __init__(self, aws_account_id, onboard=True):
        self.aws_account_id = aws_account_id
        self.onboard = onboard
        self.client = self._get_client(onboard)
        super().__init__()

    @staticmethod
    def _get_client(onboard):
        return get_credentialed_client(service_name="lambda",
                                       arns=[] if AirplaneEnv.is_local_env() else
                                       [f"arn:aws:iam::{KOS_AWS_ACCOUNT_ID}:role/SecuritySourceOnboardingRole"],
                                       desc=f"log-{'on' if onboard else 'off'}boarding-session",
                                       region="us-east-2")

    def _process_source_api_request(self, request_body, info_msg):
        print(info_msg)
        raw_rsp = self.client.invoke(
            FunctionName="panther-source-api",
            InvocationType="RequestResponse",
            Payload=bytes(json.dumps(request_body), 'utf-8'),
        )
        payload = json.loads(raw_rsp.get("Payload").read())

        if (raw_rsp.get("ResponseMetadata", {}).get("HTTPStatusCode", 0) != 200) or (raw_rsp.get("FunctionError", "")
                                                                                     == "Unhandled"):
            print("[+] Something went wrong.")
            print("[+] Request body:")
            print(request_body)
            print("[+] Response payload:")
            print(payload)
            return None
        print("Successful!")
        return payload

    def list_srcintegration_input(self):
        return {
            "listSourceIntegrations": {
                "integrationTypes": [
                    "aws-scan",
                    "aws-s3",
                ],
                "includeHealthCheck": False,
                "nameIncludes": self.aws_account_id,
                "pageSize": 25
            }
        }

    @staticmethod
    def get_delete_integration_request_body(integration_id: str):
        return {"deleteIntegration": {"integrationId": integration_id}}

    def _delete_integrations(self, source_integrations):
        integrations_to_delete = [
            integration.get("integrationId", []) for integration in source_integrations.get("integrations", [])
            if integration.get("awsAccountId", "") == self.aws_account_id
        ]

        if not integrations_to_delete:
            print(f"[+] No integrations with account id {self.aws_account_id}")
            # return will lead to airplane reporting success, which is ok in this scenario
            return

        for integration in integrations_to_delete:
            self._process_source_api_request(self.get_delete_integration_request_body(integration),
                                             info_msg=f"Deleting integration {integration}...")

    def offboard_log_integration(self):
        source_integrations = self._process_source_api_request(self.list_srcintegration_input(),
                                                               info_msg="Listing integrations...")
        if source_integrations is None:
            raise RuntimeError("Errors returned when listing out integrations. Cannot continue.")

        self._delete_integrations(source_integrations)

    def run(self):
        return None if self.onboard else self.offboard_log_integration()


@airplane.task(name=f"Offboard {TASK_NAME}", env_vars=ENV_VARS)
def offboard_hosted_account_log_sources(aws_account_id: str):
    return HostedAccountLogSources(aws_account_id=aws_account_id, onboard=False).run()


# TODO: Combine this task with offboarding task
# @airplane.task(name=f"Onboard {TASK_NAME}", env_vars=ENV_VARS)
# def onboard_hosted_account_log_sources(aws_account_id: str):
#     return HostedAccountLogSources(aws_account_id=aws_account_id).run()
