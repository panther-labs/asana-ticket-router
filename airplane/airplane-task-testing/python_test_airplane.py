import airplane

from pyshared.aws_secrets import get_secret_value
from pyshared.aws_consts import get_aws_const
from pyshared.git_ops import AirplaneMultiCloneGitTask

ENV_VARS = [
    airplane.EnvVar(name="ECS_TASK_ROLE", value="arn:aws:iam::246537256134:role/AirplaneWorkers-DynamodbReadOnly")
]


class PythonTest(AirplaneMultiCloneGitTask):

    def __init__(self):
        super().__init__(git_repos=("aws-vault-config", "hosted-aws-management", "hosted-deployments",
                                    "staging-deployments"))

    def main(self):
        print(f"Hosted DDB ARN: {get_aws_const(const_name='HOSTED_DYNAMO_RO_ROLE_ARN')}")
        return {
            "value_from_airplane_test_secret": get_secret_value("airplane/testsecret"),
            "run_url": self.get_task_run_url(),
            "task_url": self.get_task_url()
        }


@airplane.task(name=f"python-test", constraints={"ecs": "true"}, env_vars=ENV_VARS)
def python_test():
    return PythonTest().main()
