from os.path import dirname
from typing import List
import subprocess

_UTIL_PATH = f"{dirname(__file__)}/../util"


def _raise_runtime_exception(e):
    raise RuntimeError(f"command '{e.cmd}' returned with error (code {e.returncode}): {e.output}")


def setup_github():
    """Requires the DEPLOY_KEY_BASE64 environment variable to be set in the Airplane task."""
    try:
        subprocess.check_output("util/setup-github", shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        _raise_runtime_exception(e)


def git_add(files: List[str]):
    try:
        subprocess.check_output(f'{_UTIL_PATH}/git-add {" ".join(files)}', shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        _raise_runtime_exception(e)


def git_checkout(branch, create=False):
    try:
        subprocess.check_output(f"BRANCH={branch} CREATE={str(create).lower()} {_UTIL_PATH}/git-checkout",
                                shell=True,
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        _raise_runtime_exception(e)


def git_clone(repo, github_setup=False):
    if github_setup:
        setup_github()
    try:
        subprocess.check_output(f"REPOSITORY={repo} {_UTIL_PATH}/git-clone", shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        _raise_runtime_exception(e)
    return repo


def git_commit(title, description=""):
    try:
        subprocess.check_output(f'TITLE="{title}" DESCRIPTION="{description}" {_UTIL_PATH}/git-commit',
                                shell=True,
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        _raise_runtime_exception(e)


def git_push(test_run=False):
    try:
        output = subprocess.check_output(f'TEST_RUN="{str(test_run).lower()}" {_UTIL_PATH}/git-push',
                                         shell=True,
                                         stderr=subprocess.STDOUT)
        if output:
            print(output.decode())
    except subprocess.CalledProcessError as e:
        _raise_runtime_exception(e)


def git_add_commit_push(files: List[str], title, description="", test_run=False):
    git_add(files=files)
    git_commit(title=title, description=description)
    git_push(test_run=test_run)
