from pyshared.airplane_utils import AirplaneTask
from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.panther_orgs import get_panther_ou_id

_FIRST_AND_ONLY_PARENT_INDEX = 0


class AccountOuMover(AirplaneTask):

    @staticmethod
    def _get_org_role_arn(organization: str) -> str:
        if organization == "root":
            return get_aws_const("ROOT_MOVE_ACCOUNT_ROLE_ARN")
        elif organization == "hosted":
            return get_aws_const("HOSTED_MOVE_ACCOUNT_ROLE_ARN")
        raise AttributeError(f"Org role doesn't exist in {organization}.")

    def move_account_to_ou(self, organization: str, aws_account_id: str, fairytale_name: str, target_ou_name: str,
                           test_run: bool) -> None:
        org_client = get_credentialed_client(service_name="organizations",
                                             arns=self._get_org_role_arn(organization),
                                             desc=f"org_move_account_to_{target_ou_name}")
        target_ou_id = get_panther_ou_id(organization, target_ou_name)
        current_ou_id = org_client.list_parents(ChildId=aws_account_id)["Parents"][_FIRST_AND_ONLY_PARENT_INDEX]["Id"]
        current_ou = org_client.describe_organizational_unit(OrganizationalUnitId=current_ou_id)["OrganizationalUnit"]

        log_msg = f"{aws_account_id} ({fairytale_name}) from {current_ou['Name']} to {target_ou_name}"
        if test_run:
            print(f"Testing - will not move {log_msg}")
        else:
            print(f"Moving {log_msg}")
            org_client.move_account(AccountId=aws_account_id,
                                    SourceParentId=current_ou_id,
                                    DestinationParentId=target_ou_id)

    def main(self, params):
        self.move_account_to_ou(organization=params["organization"],
                                aws_account_id=params["aws_account_id"],
                                fairytale_name=params["fairytale_name"],
                                target_ou_name=params["target_ou"],
                                test_run=self.is_test_run())


def main(params: dict) -> None:
    AccountOuMover(requires_runbook=True).main(params)
