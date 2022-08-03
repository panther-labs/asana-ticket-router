from typing import List
import base64
import os
import subprocess

from git import Repo

from pyshared.airplane_utils import AirplaneTask, is_local_run
from pyshared.aws_secrets import get_secret_value
from pyshared.os_utils import tmp_change_dir


def _get_util_path():
    return f"{os.path.dirname(__file__)}/../util"


def _run_cmd(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"command '{e.cmd}' returned with error (code {e.returncode}): {e.output.decode()}")


def setup_github():
    _run_cmd(f"{_get_util_path()}/setup-github")


def git_add(files: List[str]):
    _run_cmd(f'{_get_util_path()}/git-add {" ".join(files)}')


def git_checkout(branch, create=False):
    _run_cmd(f"BRANCH={branch} CREATE={str(create).lower()} {_get_util_path()}/git-checkout")


def git_clone(repo, github_setup=False, existing_dir=None):
    if existing_dir:
        return existing_dir

    if is_local_run():
        raise RuntimeError(f"Existing directory for {repo} is not setup. "
                           "Stopping execution to prevent overriding GitHub credentials with Airplane credentials")

    if github_setup:
        setup_github()

    secret_name = _run_cmd(f"REPOSITORY={repo} {_get_util_path()}/get-deploy-key-secret-name").strip()
    with open(os.path.join(os.path.expanduser("~"), ".ssh", "id_github"), "w") as key_file:
        key_file.write(base64.b64decode(get_secret_value(secret_name=secret_name)).decode('ascii'))
    Repo.clone_from(url=f"git@github.com:panther-labs/{repo}", to_path=repo)

    return repo


def git_commit(title, description=""):
    _run_cmd(f'TITLE="{title}" DESCRIPTION="{description}" {_get_util_path()}/git-commit')


def git_push():
    output = _run_cmd(f'TEST_RUN="false" {_get_util_path()}/git-push')
    if output:
        print(output)


def _get_existing_dir(repo):
    return os.environ.get(repo, None)


def git_add_commit_push(files: List[str], title, description="", test_run=False):
    if not test_run:
        git_add(files=files)
        git_commit(title=title, description=description)
        git_push()
    else:
        print(Repo(".").git.diff())
        print(Repo(".").git.log("--graph --oneline --all --decorate -5".split()))
        print("\n\n\nYour filesystem has been changed. You may want to undo those local changes listed above")


class AirplaneMultiCloneGitTask(AirplaneTask):

    def __init__(self, git_repos):
        super().__init__()
        self.git_dirs = {
            repo: git_clone(repo=repo, github_setup=True, existing_dir=_get_existing_dir(repo))
            for repo in git_repos
        }

    def main(self):
        raise NotImplementedError


class AirplaneCloneGitTask(AirplaneTask):

    def __init__(self, params, git_repo):
        super().__init__()
        self.git_dir = git_clone(repo=git_repo, github_setup=True, existing_dir=_get_existing_dir(git_repo))

    def main_within_cloned_dir(self):
        raise NotImplementedError

    def main(self):
        with tmp_change_dir(change_dir=self.git_dir):
            return self.main_within_cloned_dir()


class AirplaneModifyGitTask(AirplaneCloneGitTask):

    def get_git_title(self):
        raise NotImplementedError

    @staticmethod
    def get_git_description(self):
        return ""

    def change_files(self) -> List[str]:
        """Will be called between a git clone and a git push, and execution of this function will take place within the
        cloned directory.

        return: A list of git paths to be committed (e.g. ["my/dir1", "my/dir2/myfile"])
        """
        raise NotImplementedError

    def checkout_new_branch(self, branch):
        git_checkout(branch, create=True)

    def main_within_cloned_dir(self):
        """Make a change to files in a repo then commit them (if the environment is staging or prod)."""
        modified_files = self.change_files()
        return git_add_commit_push(files=modified_files,
                                   title=self.get_git_title(),
                                   description=self.get_git_description(),
                                   test_run=self.is_test_run())
