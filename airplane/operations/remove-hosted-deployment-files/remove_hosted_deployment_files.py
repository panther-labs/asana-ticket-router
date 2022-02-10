# Linked to https://app.airplane.dev/t/remove_hosted_deployment_files [do not edit this line]
import glob
import os

from pyshared.git_ops import git_add_commit_push, git_clone


def remove_hosted_deployment_files(fairytale_name, hosted_deploy_dir, test_run):
    if hosted_deploy_dir is None:
        hosted_deploy_dir = git_clone(repo="hosted-deployments", github_setup=True)

    prev_path = os.getcwd()
    try:
        os.chdir(hosted_deploy_dir)
        delete_filepaths = glob.glob(f"**/*{fairytale_name}*", recursive=True)
        print(f"Going to delete the following files: {delete_filepaths}")
        for delete_filepath in delete_filepaths:
            os.remove(delete_filepath)
        if delete_filepaths:
            git_add_commit_push(files=delete_filepaths, title=f"Remove {fairytale_name} account", test_run=test_run)
    finally:
        os.chdir(prev_path)


def main(params):
    remove_hosted_deployment_files(fairytale_name=params["fairytale_name"],
                                   hosted_deploy_dir=params.get("hosted_deploy_dir"),
                                   test_run=params["airplane_test_run"])