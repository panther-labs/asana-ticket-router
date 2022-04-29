from dataclasses import asdict, dataclass

from pyshared.aws_creds import get_credentialed_resource, get_credentialed_client
from pyshared.aws_consts import get_aws_const
from pyshared.deployments_file import get_deployment_filepath, DeploymentsRepo
from pyshared.git_ops import AirplaneCloneGitTask
from pyshared.yaml_utils import load_yaml_cfg

DEFAULT_MASTER_STACK_NAME = "panther"
CUSTOMER_TEARDOWN_ROLE_ARN = get_aws_const(const_name="CUSTOMER_TEARDOWN_ROLE_ARN")


@dataclass
class AirplaneParams:
    fairytale_name: str
    aws_account_id: str
    region: str
    airplane_test_run: bool


class DeleteCustomerMasterStack(AirplaneCloneGitTask):

    def __init__(self, params):
        super().__init__(params=params, git_repo=DeploymentsRepo.HOSTED)
        self.airplane_params = AirplaneParams(**params)

    def main_within_cloned_dir(self):
        master_stack_name = self.get_master_stack_name()
        self.delete_master_stack(stack_name=master_stack_name)

    @staticmethod
    def get_customer_teardown_role_arns(aws_account_id: str) -> tuple[str, str]:
        return CUSTOMER_TEARDOWN_ROLE_ARN, f"arn:aws:iam::{aws_account_id}:role/PantherTeardownRole"

    def get_master_stack_name(self) -> str:
        deployment_file = get_deployment_filepath(fairytale_name=self.airplane_params.fairytale_name)
        try:
            cfn_yaml = load_yaml_cfg(cfg_filepath=deployment_file,
                                     error_msg=f"Customer deployment file not found: '{deployment_file}'")
            return cfn_yaml.get("PantherStackName", DEFAULT_MASTER_STACK_NAME)
        except ValueError as e:
            print(e)
            return DEFAULT_MASTER_STACK_NAME

    def delete_master_stack(self, stack_name: str) -> None:
        cfn_kwargs = {
            "service_name": "cloudformation",
            "arns": self.get_customer_teardown_role_arns(self.airplane_params.aws_account_id),
            "desc": f"cfn_remove_{self.airplane_params.fairytale_name}_master_stack",
            "region": self.airplane_params.region,
            "test_role": self.test_roles.get("customer_support_role")
        }
        stack = get_credentialed_resource(**cfn_kwargs).Stack(stack_name)

        if self.airplane_params.airplane_test_run:
            print(f"Test run, not deleting the '{stack.name}' stack.")
            return

        # Delete the stack
        stack.delete()
        print(f"Initiated '{stack_name}' stack deletion.")

        # Temporary: Disable waiter for shorter execution times
        # # The waiter will make at most 60 attempts with 60s interval in between
        # waiter_cfg = {"MaxAttempts": 60, "Delay": 60}
        #
        # # Wait for status 'stack_delete_complete'
        # get_credentialed_client(**cfn_kwargs) \
        #     .get_waiter("stack_delete_complete") \
        #     .wait(StackName=stack_name, WaiterConfig=waiter_cfg)
        #
        # print(f"Deleted the '{stack_name}' stack")


def main(params):
    DeleteCustomerMasterStack(params).main()


def test_manual():
    DeleteCustomerMasterStack.add_test_role(role_key="customer_support_role",
                                            role_value="hosted-tangible-dinosaur-support")
    params = AirplaneParams(fairytale_name="tangible-dinosaur",
                            aws_account_id="280391971082",
                            region="us-west-2",
                            airplane_test_run=True)
    main(asdict(params))
