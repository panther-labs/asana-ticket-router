# Linked to https://app.airplane.dev/t/python_test [do not edit this line]
from pyshared.airplane_utils import AirplaneTask
from pyshared.aws_secrets import get_secret_value
from pyshared.aws_consts import get_aws_const
from pyshared.git_ops import git_clone, AirplaneMultiCloneGitTask


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


def main(_):
    return PythonTest().main()
