from consts.aws_account_id import AccountName, AccountId
from consts.aws_arn import get_arn


class AwsResources(AccountId):

    def __init__(self, account_name: AccountName):
        super().__init__(account_name=account_name)
        self.DEPLOYMENT_QUEUE = None
        self.DEPLOYMENT_METADATA_TABLE = None
        self.DEPLOYMENT_STEP_FUNCTION_ARN = None

        {
            AccountName.HOSTED_OPS: lambda: None,
            AccountName.HOSTED_ROOT: self._init_hosted_root_resources,
            AccountName.PANTHER_ROOT: self._init_panther_root_resources
        }[account_name]()

    def _init_hosted_root_resources(self):
        self.CERT_LAMBDA_ARN = get_arn(
            service="lambda",
            account_id=self.account_id,
            resource_name="function:hosted-deployments-CertCreatorLambdaFunction-QVSQDCKLXRL6")
        self.DEPLOYMENT_QUEUE = "deployment.fifo"
        self.DEPLOYMENT_METADATA_TABLE = "hosted-deployments-DeploymentMetadataTable-22PITRD2LM2B"
        self.DEPLOYMENT_STEP_FUNCTION_ARN = get_arn(
            service="states",
            account_id=self.account_id,
            resource_name="stateMachine:AutomatedDeploymentStateMachine-y5bh5L9a5z41",
            region="us-west-2")

    def _init_panther_root_resources(self):
        self.CERT_LAMBDA_ARN = get_arn(
            service="lambda",
            account_id=self.account_id,
            resource_name="function:hosted-deployments-CertCreatorLambdaFunction-1N6ELEBE1PBGA")
        self.DEPLOYMENT_QUEUE = "deployment.fifo"
        self.DEPLOYMENT_METADATA_TABLE = "hosted-deployments-DeploymentMetadataTable-PXJR2DWAF84N"
        self.DEPLOYMENT_STEP_FUNCTION_ARN = get_arn(
            service="states",
            account_id=self.account_id,
            resource_name="stateMachine:AutomatedDeploymentStateMachine-Sysh4tP2b9tu",
            region="us-west-2")
