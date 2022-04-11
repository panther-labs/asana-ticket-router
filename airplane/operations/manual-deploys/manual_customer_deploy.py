import datetime

from pyshared.deployments_file import DeploymentsRepo, alter_deployment_file
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg


def update_cfg_file(filepath):
    cfg = load_yaml_cfg(cfg_filepath=filepath, error_msg=f"Customer deployment file not found: '{filepath}'")
    cfg["ManualDeploy"] = str(datetime.datetime.now())
    save_yaml_cfg(cfg_filepath=filepath, cfg=cfg)


def main(params):
    alter_deployment_file(deployments_repo=DeploymentsRepo.HOSTED,
                          ap_params=params,
                          alter_callable=update_cfg_file,
                          commit_title=f"Manually redeploy {params['fairytale_name']}")
