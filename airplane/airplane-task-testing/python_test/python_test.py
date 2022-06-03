# Linked to https://app.airplane.dev/t/python_test [do not edit this line]
from pyshared.aws_secrets import get_secret_value
from pyshared.aws_consts import get_aws_const
from pyshared.git_ops import AirplaneMultiCloneGitTask
from pyshared.airplane_utils import AirplaneTask as ApTaskV1
from v2.task_models.airplane_task import AirplaneTask as ApTaskV2


class PythonTest(AirplaneMultiCloneGitTask):

    def __init__(self):
        super().__init__(git_repos=("aws-vault-config", "hosted-aws-management", "hosted-deployments",
                                    "staging-deployments"))

    def main(self):
        print(f"Hosted DDB ARN: {get_aws_const(const_name='HOSTED_DYNAMO_RO_ROLE_ARN')}")
        return {
            "value_from_airplane_test_secret": get_secret_value("airplane/testsecret"),
            "run_url": self.get_run_url(),
            "task_url": self.get_task_url()
        }


class PythonTest1FailureNotifications(ApTaskV1):
    def main(self, params: dict):
        raise RuntimeError("Testing an exception message sent through Slack")

    def get_failure_slack_channel(self):
        return "#tscott-testing"


class PythonTest2FailureNotifications(ApTaskV2):
    def run(self, params: dict):
        raise ValueError("Is this message printed to a Slack channel?")

    def get_failure_slack_channel(self):
        return "#tscott-testing"


def main(_):
    # Notice: Any return values are not going to get returned from these
    PythonTest1FailureNotifications().main_notify_failures()
    PythonTest2FailureNotifications().run_notify_failures()

    return PythonTest().main()
