import os

from botocore.exceptions import ClientError

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.deprov_info import DeprovInfoDeployFile
from v2.consts.airplane_env import AirplaneEnv
from v2.pyshared.deployments_file import get_customer_deployment_filepath, get_github_repo_from_organization, generate_configs
from v2.pyshared.os_util import tmp_change_dir
from v2.task_models.airplane_git_task import AirplaneGitTask


class DnsRecordRemover(AirplaneGitTask):

    @staticmethod
    def get_delete_stack_role_arn(organization: str) -> str:
        if organization == "root":
            return get_aws_const("ROOT_CFN_DELETE_STACK_ROLE_ARN")
        elif organization == "hosted":
            return get_aws_const("HOSTED_CFN_DELETE_STACK_ROLE_ARN")
        raise AttributeError(f"Role doesn't exist in {organization}.")

    def delete_dns_records(self, organization: str, fairytale_name: str) -> bool:
        cfn_kwargs = {
            "service_name": "cloudformation",
            "arns": self.get_delete_stack_role_arn(organization),
            "desc": f"cfn_remove_dns_records",
            "region": "us-west-2"
        }
        cfn_client = get_credentialed_client(**cfn_kwargs)
        cfn_waiter = cfn_client.get_waiter("stack_delete_complete")

        is_stack_deleted = False
        stack_names = [f"route53-{fairytale_name}", f"panther-cert-{fairytale_name}"]
        for stack_name in stack_names:
            try:
                # Try to find the stack by name, raises an error if doesn't exist
                cfn_client.describe_stacks(StackName=stack_name)
                cfn_client.delete_stack(StackName=stack_name)
                cfn_waiter.wait(StackName=stack_name, WaiterConfig={"Delay": 30, "MaxAttempts": 20})
                print(f"Deleted '{stack_name}' stack.")
                is_stack_deleted = True
            except ClientError:
                print(f"Stack '{stack_name}' doesn't exist or is already deleted.")

        return is_stack_deleted

    def _remove_from_deprov_info(self, fairytale_name, organization):
        repo_name = get_github_repo_from_organization(organization)
        git_dir = self.clone_repo_or_get_local(repo_name=repo_name, local_repo_abs_path=os.getenv(repo_name))
        with tmp_change_dir(git_dir):
            deprov_info_deploy_file = DeprovInfoDeployFile(filepath=get_customer_deployment_filepath(fairytale_name))
            deprov_info_deploy_file.remove_dns_time()
            generate_configs()
            self.git_add_commit_and_push(title=f"DNS teardown complete for {fairytale_name}")

    def run(self, params):
        fairytale_name = params["fairytale_name"]
        aws_account_id = params["aws_account_id"]
        deprov_slack_msg = (
            f"Account {aws_account_id}/{fairytale_name} is being deprovisioned "
            f"(see {AirplaneEnv.get_task_run_url()}).\n\n"
            f"Requestor email: {AirplaneEnv.AIRPLANE_REQUESTER_EMAIL}, team ID: {AirplaneEnv.AIRPLANE_TEAM_ID}")

        # Send Jay Rosenthal a message for data-analytics-gathering purposes
        jrosenthal_slack_id = "U037VGD4ZFC"
        self.send_slack_message(channel_name=jrosenthal_slack_id, message=deprov_slack_msg)

        is_stack_deleted = self.delete_dns_records(organization=params["organization"], fairytale_name=fairytale_name)
        if is_stack_deleted:
            self.send_slack_message(channel_name="#security-alerts-high-pri", message=deprov_slack_msg)

        self._remove_from_deprov_info(fairytale_name=params["fairytale_name"], organization=params["organization"])


def main(params):
    DnsRecordRemover(requires_runbook=True).run(params)
