import airplane

from consts.aws_account_id import AccountId, AccountName
from consts.aws_arn import get_arn


class Role(AccountId):

    def get_role_arn(self, role_name: str):
        return get_arn(service="iam", account_id=self.account_id, resource_name=f"role/{role_name}")


class AirplaneEcsEnvVar(Role):

    def __init__(self):
        super().__init__(account_name=AccountName.HOSTED_OPS)
        self.CUSTOMER_DEPLOYMENT = self.get_env_var("AirplaneWorkers-CustomerDeployment")

    def get_env_var(self, role_name: str):
        return airplane.EnvVar(name="ECS_TASK_ROLE", value=self.get_role_arn(role_name))


class AirplaneTaskRole(Role):

    def __init__(self, account_name: str):
        super().__init__(account_name=account_name)
        self.CUSTOMER_DEPLOYMENT = self.get_role_arn("AirplaneCustomerDeployment")


class AwsRole(Role):

    def __init__(self, account_name: str):
        super().__init__(account_name=account_name)
        self.CERT_LAMBDA_ROLE = None
        self.CUSTOMER_DEPLOYMENT = self.get_role_arn("CustomerDeployment")

        {
            AccountName.HOSTED_OPS: lambda: None,
            AccountName.HOSTED_ROOT: self._init_hosted_root_resources,
            AccountName.PANTHER_ROOT: self._init_panther_root_resources
        }[account_name]()

    def _init_hosted_root_resources(self):
        self.CERT_LAMBDA_ROLE = self.get_role_arn("hosted-deployments-CertCreatorLambdaRole-1KNU3G8ARXPYU")

    def _init_panther_root_resources(self):
        self.CERT_LAMBDA_ROLE = self.get_role_arn("hosted-deployments-CertCreatorLambdaRole-8AALO976MRR5")
