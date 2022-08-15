import os

from v2.task_models.airplane_git_task import AirplaneGitTask
from v2.consts.airplane_env import AirplaneEnv
from v2.consts.deployment_groups import HostedDeploymentGroup
from v2.consts.github_repos import GithubRepo
from v2.pyshared.deployments_file import create_customer_file, generate_fairytale_name, \
    get_customer_deployment_filepath, get_deployment_metadata_dir
from v2.pyshared.panther_version_util import get_version_from_template_url
from v2.pyshared.os_util import tmp_change_dir
from v2.pyshared.yaml_utils import load_yaml_cfg


class NewCustomerCreator(AirplaneGitTask):

    def __init__(self, is_dry_run=False):
        super().__init__(is_dry_run=is_dry_run)
        self.deploys_path = self.clone_repo_or_get_local(repo_name=GithubRepo.HOSTED_DEPLOYMENTS,
                                                         local_repo_abs_path=os.getenv(GithubRepo.HOSTED_DEPLOYMENTS))

    def _translate_params_to_customer_cfg(self, params):
        cfg = {
            "contact_first_name": params["first_name"],
            "contact_last_name": params["last_name"],
            "contact_email": params["email_address"],
            "customer_display_name": params["account_name"],
            "customer_id": params.get("fairytale_name", generate_fairytale_name(repo_path=self.deploys_path)),
            "group": params["deploy_group"].lower(),
            "deploy_method": "template",
            "service_type": params.get("service_type", "SaaS"),
            "region": params["region"],
            "snowflake_deployment": params["backend"],
            "sales_customer_id": params["sales_customer_id"],
            "sales_phase": params["sales_phase"],
            "sales_opportunity_id": params["sales_opportunity_id"],
        }

        if "customer_domain" in params:
            cfg["customer_domain"] = params["customer_domain"]

        return cfg

    def _get_customer_version(self, fairytale_name):
        cfg = load_yaml_cfg(cfg_filepath=get_customer_deployment_filepath(
            fairytale_name=fairytale_name, repo_path=self.deploys_path, get_generated_filepath=True))
        return get_version_from_template_url(template_url=cfg["PantherTemplateURL"])

    def run(self, params):
        if not HostedDeploymentGroup.is_hosted_deployment_group(params["deploy_group"]):
            raise ValueError(
                f"Invalid deploy group of {params['deploy_group']}. Choose from {HostedDeploymentGroup.get_values()}")
        fairytale_name = create_customer_file(repo_path=self.deploys_path,
                                              customer_cfg=self._translate_params_to_customer_cfg(params))
        panther_version = self._get_customer_version(fairytale_name)
        with tmp_change_dir(self.deploys_path):
            self.git_add_commit_and_push(title=f"Creating customer {params['account_name']}",
                                         filepaths=get_deployment_metadata_dir(repo_path=self.deploys_path))
        return {"fairytale_name": fairytale_name, "panther_version": panther_version}


def main(params):
    return NewCustomerCreator(is_dry_run=(not AirplaneEnv.is_prod_env())).run(params)
