import os

from pyshared.deployments_file import DeploymentsRepo, alter_deployment_file


def main(params):
    alter_deployment_file(deployments_repo=DeploymentsRepo.HOSTED,
                          ap_params=params,
                          alter_callable=lambda filepath: os.remove(filepath),
                          commit_title=f"Removing deployment files for {params['fairytale_name']}",
                          apply_to_generated_file=True)
