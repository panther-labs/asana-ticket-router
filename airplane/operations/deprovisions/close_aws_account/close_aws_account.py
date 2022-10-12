from dataclasses import dataclass
from tenacity import retry, retry_if_result, stop_after_delay, wait_fixed

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.airplane_utils import AirplaneTask


def print_after_query(_):
    print("Closing account and waiting for SUSPENDED status...")


def raise_exception_if_closing_takes_too_long(_):
    raise RuntimeError(f"Timed out waiting for account to close")


@dataclass
class AirplaneParams:
    aws_account_id: str
    organization: str


class AccountCloser(AirplaneTask):

    def main(self, params):
        ap_params = AirplaneParams(**params)
        # Only accounts with a specific AWS tag can be deleted by this role.
        client = get_credentialed_client(service_name="organizations",
                                         arns=get_aws_const(f"{ap_params.organization.upper()}_CLOSE_ACCOUNT_ROLE_ARN"),
                                         desc=f"closing_aws_account_{ap_params.aws_account_id}")
        try:
            client.close_account(AccountId=ap_params.aws_account_id)
        except Exception as exc:
            if exc.response["Error"]["Code"] == "AccountAlreadyClosedException":
                print("Account is already closed. Doing nothing.")
            else:
                raise exc

        account_status = self._wait_for_account_closure_completion(client, ap_params.aws_account_id)
        if account_status != "SUSPENDED":
            raise RuntimeError(f"Closing account failed with status {account_status}")

    @retry(after=print_after_query,
           retry=retry_if_result(lambda account_status: account_status == "PENDING_CLOSURE"),
           retry_error_callback=raise_exception_if_closing_takes_too_long,
           stop=stop_after_delay(600),
           wait=wait_fixed(15))
    def _wait_for_account_closure_completion(self, client, aws_account_id):
        return client.describe_account(AccountId=aws_account_id)["Account"]["Status"]


def main(params):
    AccountCloser().main(params)
