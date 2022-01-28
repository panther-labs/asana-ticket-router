from os.path import dirname
from typing import List
import subprocess

_UTIL_PATH = f"{dirname(__file__)}/../util"


def setup_github():
    """Requires the DEPLOY_KEY_BASE64 environment variable to be set in the Airplane task."""
    subprocess.run("util/setup-github")


def git_add(files: List[str]):
    subprocess.run(f'{_UTIL_PATH}/git-add {" ".join(files)}', shell=True)


def git_checkout(branch, create=False):
    subprocess.run(f"BRANCH={branch} CREATE={str(create).lower()} {_UTIL_PATH}/git-checkout", shell=True)


def git_clone(repo, github_setup=False):
    if github_setup:
        setup_github()
    subprocess.run(f"REPOSITORY={repo} {_UTIL_PATH}/git-clone", shell=True)
    return repo


def git_commit(title, description=""):
    subprocess.run(f'TITLE="{title}" DESCRIPTION="{description}" {_UTIL_PATH}/git-commit', shell=True)
    return


def git_push(test_run=False):
    subprocess.run(f'TEST_RUN="{str(test_run).lower()}" {_UTIL_PATH}/git-push', shell=True)
    return
