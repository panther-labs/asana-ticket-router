import datetime

from pyshared.deployments_file import DeploymentsRepo, alter_deployment_file


def add_deprovisioning_tags(filepath):
    marked_tag = "# Marked for deletion"
    with open(filepath, "r+") as deploy_file:
        contents = deploy_file.read()
        if marked_tag in contents:
            raise RuntimeError(f"This deployment is already marked for deletion! Cannot mark it again.")
        deploy_file.seek(0, 0)
        eight_days = str((datetime.datetime.today() + datetime.timedelta(days=8)).date())
        deploy_file.write(f"{marked_tag}: {eight_days}\n{contents}")


def main(params):
    alter_deployment_file(deployments_repo=DeploymentsRepo.HOSTED,
                          ap_params=params,
                          alter_callable=add_deprovisioning_tags,
                          commit_title=f"Mark {params['fairytale_name']} for deprovisioning")
