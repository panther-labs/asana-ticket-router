from os.path import dirname
from typing import List
import subprocess

from pyshared.aws_secrets import get_secret_value

_UTIL_PATH = f"{dirname(__file__)}/../util"


def _run_cmd(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"command '{e.cmd}' returned with error (code {e.returncode}): {e.output.decode()}")


def setup_github():
    _run_cmd("util/setup-github")


def git_add(files: List[str]):
    _run_cmd(f'{_UTIL_PATH}/git-add {" ".join(files)}')


def git_checkout(branch, create=False):
    _run_cmd(f"BRANCH={branch} CREATE={str(create).lower()} {_UTIL_PATH}/git-checkout")


def git_clone(repo, github_setup=False, existing_dir=None):
    if existing_dir:
        return existing_dir

    if github_setup:
        setup_github()

    secret_name = _run_cmd(f"REPOSITORY={repo} {_UTIL_PATH}/get-deploy-key-secret-name").strip()
    deploy_key_base64 = get_secret_value(secret_name=secret_name)
    _run_cmd(f"REPOSITORY={repo} DEPLOY_KEY_BASE64={deploy_key_base64} {_UTIL_PATH}/git-clone")

    return repo


def git_commit(title, description=""):
    _run_cmd(f'TITLE="{title}" DESCRIPTION="{description}" {_UTIL_PATH}/git-commit')


def git_push(test_run=False):
    output = _run_cmd(f'TEST_RUN="{str(test_run).lower()}" {_UTIL_PATH}/git-push')
    if output:
        print(output)


def git_add_commit_push(files: List[str], title, description="", test_run=False):
    git_add(files=files)
    git_commit(title=title, description=description)
    git_push(test_run=test_run)
