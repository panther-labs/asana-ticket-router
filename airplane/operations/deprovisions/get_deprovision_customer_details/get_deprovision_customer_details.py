from dataclasses import dataclass

from pyshared.customer_info_retriever import AllCustomerAccountsInfo
from pyshared.panther_orgs import get_panther_org
from v2.consts.airplane_env import AirplaneEnv
from v2.exceptions import DuplicateAwsAccountIdException, DuplicateNotionFairytaleNameException, \
    InvalidFairytaleNameException, InvalidRegionException
from v2.task_models.airplane_git_task import AirplaneGitTask


@dataclass
class AirplaneParams:
    fairytale_name: str
    org_name: str
    region: str = ""


class DeploymentCustomerDetails(AirplaneGitTask):
    DESIRED_NUM_AWS_ACCOUNT_IDS = 1

    def __init__(self):
        super().__init__()
        self.all_accounts_info = AllCustomerAccountsInfo()
        self.warnings = {}
        self.aws_account_id = None
        self.all_accounts_with_aws_id = []
        self.accounts_per_region = {}

    def run(self, params: dict):
        ap_params = AirplaneParams(**params)
        # Validates org name
        get_panther_org(ap_params.org_name)

        dynamo, dynamo_results = self._retrieve_accounts_info(ap_params)
        self.aws_account_id = dynamo["AWSConfiguration"]["AccountId"]
        self._retrieve_accounts_with_aws_id_from_dynamo(all_dynamo_results=dynamo_results)

        self._check_for_no_duplicate_fairytale_names_in_notion(ap_params.fairytale_name)
        self._check_exactly_one_ddb_entry_has_same_aws_id_and_same_region(
            ap_params.region) if ap_params.region else self._check_only_one_aws_account_found()

        if AirplaneEnv.is_api_user_execution():
            if self.warnings:
                message = ("API attempt to get customer details failed.\n"
                           f"Warnings: {self.warnings}\n"
                           f"Fairytale Name: {ap_params.fairytale_name}")
                self.send_slack_message(channel_name="#triage-deployment", message=message)
                raise RuntimeError(message)

        return {
            "account_id": self.aws_account_id,
            "is_safe_to_close": not self.warnings,
            "company_display_name": dynamo["GithubCloudFormationParameters"]["CompanyDisplayName"],
            "domain": dynamo["GithubCloudFormationParameters"]["CustomDomain"],
            "org": ap_params.org_name,
            "region": dynamo["GithubConfiguration"]["CustomerRegion"],
            "warnings": self.warnings,
        }

    def _retrieve_accounts_info(self, ap_params: AirplaneParams) -> (dict, dict[str, dict]):
        notion_results = self.all_accounts_info.get_notion_results()
        dynamo_results = self.all_accounts_info.get_dynamo_results(get_hosted=(ap_params.org_name == "hosted"),
                                                                   get_staging=(ap_params.org_name == "root"))
        try:
            notion_results[ap_params.fairytale_name]
            return dynamo_results[ap_params.fairytale_name], dynamo_results
        except KeyError:
            raise InvalidFairytaleNameException(fairytale_name=ap_params.fairytale_name)

    def _check_for_no_duplicate_fairytale_names_in_notion(self, fairytale_name: str) -> None:
        if fairytale_name in self.all_accounts_info.get_notion_duplicates():
            raise DuplicateNotionFairytaleNameException(fairytale_name=fairytale_name)

    def _check_only_one_aws_account_found(self):
        if len(self.all_accounts_with_aws_id) > self.DESIRED_NUM_AWS_ACCOUNT_IDS:
            raise DuplicateAwsAccountIdException("Multiple DynamoDB entries found with AWS account ID "
                                                 f"{self.aws_account_id}: {self.all_accounts_with_aws_id}")

    def _check_exactly_one_ddb_entry_has_same_aws_id_and_same_region(self, region):
        # No DDB entries found with AWS account ID and region - an invalid condition
        try:
            ft_names_using_region = self.accounts_per_region[region]
        except KeyError:
            raise InvalidRegionException(region=region, aws_account_id=self.aws_account_id)

        # Multiple DDB entries found with same AWS account ID and region - an invalid condition
        if len(ft_names_using_region) > self.DESIRED_NUM_AWS_ACCOUNT_IDS:
            raise DuplicateAwsAccountIdException(
                f"The following fairytale names have the same region '{region}' and AWS account ID in DynamoDB: "
                f"{ft_names_using_region}")

        # Multiple DDB entries found with same AWS account ID but different regions - a valid condition
        # (for instance, customer has multiple Panther instances in same account but different regions)
        elif len(self.all_accounts_with_aws_id) > self.DESIRED_NUM_AWS_ACCOUNT_IDS:
            self.warnings["multiple_accounts"] = (
                "These fairytale names use the same account but have different regions: "
                f"{self.all_accounts_with_aws_id}")

    def _retrieve_accounts_with_aws_id_from_dynamo(self, all_dynamo_results: dict[str, dict]) -> None:
        for fairytale_name, dynamo in all_dynamo_results.items():
            if dynamo.get("AWSConfiguration", {}).get("AccountId", "") == self.aws_account_id:
                region = all_dynamo_results[fairytale_name]["GithubConfiguration"]["CustomerRegion"]
                self.accounts_per_region.setdefault(region, []).append(fairytale_name)
                self.all_accounts_with_aws_id.append(fairytale_name)

    def get_failure_slack_channel(self):
        return "#triage-deployment"


def main(params):
    return DeploymentCustomerDetails().run_notify_failures(params)
