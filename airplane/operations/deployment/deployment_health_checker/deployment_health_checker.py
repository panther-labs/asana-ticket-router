from pyshared.airplane_utils import AirplaneTask
from pyshared.customer_info_retriever import AllCustomerAccountsInfo
from pyshared.notion_databases import AccountsDatabaseSchema
from v2.consts.depoyment_groups import HostedDeploymentGroup
from v2.pyshared.date_utils import Timezone, get_day_of_week_name, get_today
from v2.pyshared.panther_version_util import to_semver


class DeploymentHealthChecker(AirplaneTask):

    def __init__(self):
        self.notion_entries = AllCustomerAccountsInfo().get_notion_results(include_deprovisioned=False)

    def _get_unfinished_airplane_creation_accounts(self):
        return [
            fairytale_name for fairytale_name, notion_info in self.notion_entries.items()
            if (notion_info.Airplane_Creation_Link and not notion_info.Airplane_Creation_Completed)
        ]

    def _get_mismatched_panther_versions(self):

        def versions_do_not_match(notion_info):
            return notion_info.Actual_Version and notion_info.Expected_Version and (notion_info.Actual_Version !=
                                                                                    notion_info.Expected_Version)

        return [{
            fairytale_name: {
                "Expected Version": notion_info.Expected_Version,
                "Actual Version": notion_info.Actual_Version
            }
        } for fairytale_name, notion_info in self.notion_entries.items() if versions_do_not_match(notion_info)]

    def _get_deploy_group_inconsistency(self, latest_deployed_ga_version):
        # Only check on non-upgrade days. This likely isn't the best way to do this, but it works for now.
        if get_day_of_week_name(get_today(Timezone.PDT)) in ("Tuesday", "Wednesday"):
            return []
        inconsistencies = []

        for fairytale_name, notion_info in self.notion_entries.items():
            if not self._has_actual_version_and_hosted_deploy_group(notion_info):
                continue
            version = to_semver(notion_info.Actual_Version)
            if (version.major != latest_deployed_ga_version.major) or (version.minor !=
                                                                       latest_deployed_ga_version.minor):
                inconsistencies.append(fairytale_name)

        return inconsistencies

    def _get_latest_deployed_ga_version(self):
        panther_versions = tuple((to_semver(notion_entry.Actual_Version)
                                  for notion_entry in self.notion_entries.values()
                                  if self._has_actual_version_and_hosted_deploy_group(notion_entry)))
        return max(panther_versions) if panther_versions else to_semver("0.0.0")

    @staticmethod
    def _has_actual_version_and_hosted_deploy_group(notion_entry: AccountsDatabaseSchema):
        return (notion_entry.Actual_Version and notion_entry.Deploy_Group
                and HostedDeploymentGroup.is_hosted_deployment_group(notion_entry.Deploy_Group))

    def main(self, params):
        latest_deployed_ga_version = self._get_latest_deployed_ga_version()

        return {
            "unfinished_airplane": self._get_unfinished_airplane_creation_accounts(),
            "mismatched_panther_versions": self._get_mismatched_panther_versions(),
            "deploy_group_inconsistency": self._get_deploy_group_inconsistency(latest_deployed_ga_version),
            "runbook_url": self.get_runbook_run_url(),
            "latest_deployed_ga_version": str(latest_deployed_ga_version),
        }

    def get_failure_slack_channel(self):
        return "#triage-productivity"


def main(_):
    return DeploymentHealthChecker().main_notify_failures({})
