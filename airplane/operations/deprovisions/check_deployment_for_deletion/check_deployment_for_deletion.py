import datetime as datetime
from pyshared.airplane_utils import AirplaneTask
from pyshared.deployments_file import DeploymentsRepo, get_deployment_targets_dir
from pyshared.git_ops import git_clone
from pyshared.os_utils import list_files
from pyshared.date_utils import get_today, get_tomorrow, to_date_str


class DeploymentDeletionChecker(AirplaneTask):
    def main(self, params):
        return self.find_customers_close_to_deletion()

    def get_failure_slack_channel(self):
        return "#triage-productivity"

    @staticmethod
    def find_customers_close_to_deletion():
        hosted_deploy_dir = git_clone(repo=DeploymentsRepo.HOSTED, github_setup=True)
        deployment_targets_dir = get_deployment_targets_dir(hosted_deploy_dir)
        files = list_files(deployment_targets_dir)
        output = {'one-day-delete': [], 'zero-day-delete': []}
        for file in files:
            with open(deployment_targets_dir + "/" + file) as f:
                first_line = f.readline().lower()
                if first_line.startswith('# marked for deletion:'):
                    date_string = first_line.removeprefix('# marked for deletion:').strip()
                    deletion_date = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
                    if deletion_date == to_date_str(get_today()):
                        output['zero-day-delete'].append(file.removesuffix('.yml'))
                    elif deletion_date == to_date_str(get_tomorrow()):
                        output['one-day-delete'].append(file.removesuffix('.yml'))

        return output


def main(params):
    return DeploymentDeletionChecker().main_notify_failures(params)
