"""
git_util contains a Class that handles functionality for
interacting with Git repositories
"""

import base64
import json

import boto3
from git import Repo
from git import cmd as git_cmd
from tenacity import retry, stop_after_attempt, wait_fixed

from os_util import join_paths, change_mode, run_cmd


class GitRepo:
    """
    GitRepo contains methods around handling various Git operations.
    """

    def __init__(self, path: str, repo_name: str, branch_name: str):
        if not self._is_supported_repo(repo_name):
            raise AttributeError(f"Repo '{repo_name}' isn't supported.")
        self.name = repo_name
        self.branch_name = branch_name
        self.repo_url = f"git@github.com:panther-labs/{repo_name}.git"
        self.path = join_paths(path, repo_name)
        self._ssh_key_path = join_paths(path, 'id_rsa')
        self._known_hosts_path = join_paths(path, 'known_hosts')
        self._setup_auth()
        self.repo = self._clone()
        self._setup_github_user()

    @staticmethod
    def _is_supported_repo(repo_name: str) -> bool:
        """
        _is_supported_repo determines if a GitHub repository can
        utilize the GitRepo class functionality
        """
        return repo_name in ["hosted-deployments", "staging-deployments"]

    def _get_repo_ssh_key(self) -> str:
        """
        _get_repo_ssh_key returns the SSH key used for GitHub operations
        """
        client = boto3.client("secretsmanager")
        secret_name = f"airplane/{self.name}-deploy-key-base64"
        response = json.loads(client.get_secret_value(SecretId=secret_name)["SecretString"])
        secret_b64 = list(response.values())[0]
        return base64.b64decode(secret_b64).decode('ascii')

    def _setup_auth(self) -> None:
        """
        _setup_auth modifies the repo SSH key, sets its mode, and performs a key scan
        to add the public GitHub keys to the known hosts file
        """
        ssh_key = self._get_repo_ssh_key()
        with open(self._ssh_key_path, "w", encoding="utf-8") as fileobj:
            fileobj.write(f"{ssh_key}\n")
        change_mode(self._ssh_key_path, 0o600)
        print(f"Saved an ssh key for '{self.name}' to: {self._ssh_key_path}")
        run_cmd(f"ssh-keyscan github.com > {self._known_hosts_path}")
        print(f"Added github.com to known hosts at: {self._known_hosts_path}")

    def _clone(self) -> Repo:
        """
        _clone performs a git clone for a given repository
        """
        print(f"Cloning repo to: {self.path}")
        return Repo.clone_from(
            url=self.repo_url,
            branch=self.branch_name,
            to_path=self.path,
            env={
                "GIT_SSH_COMMAND":
                    f"ssh -o UserKnownHostsFile={self._known_hosts_path} -i {self._ssh_key_path}"
            }
        )  # pylint: disable=C0301

    def _setup_github_user(self) -> None:
        """
        _setup_github_user modifies the gitconfig fields for user.email and user.name
        """
        git_config = self.repo.config_writer()
        git_config.set_value("user", "email", "github-service-account@runpanther.io")
        git_config.set_value("user", "name", "panther-bot")
        git_config.release()

    def _diff(self) -> str:
        """
        _diff performs a git diff on modified files
        """
        return self.repo.git.diff()

    def add(self, filepaths: list[str] = None) -> str:
        """
        add runs git add to stage a list of files for committing
        """
        if not filepaths:
            filepaths = [self.path]
        return self.repo.index.add(filepaths)

    def _commit(self, title: str, description: str = "") -> None:
        """
        _commit performs a git commit for staged files
        """
        if description:
            title = f"{title}\n\n{description}"
        self.repo.index.commit(message=title)

    @staticmethod
    def _pull_rebase() -> None:
        """
        _pull_rebase runs a git pull --rebase
        """
        print("Running 'git pull --rebase'")
        git_cmd.Git().pull('--rebase')

    @retry(
        wait=wait_fixed(30),
        stop=stop_after_attempt(3),
        after=lambda _: GitRepo._pull_rebase(),
        reraise=True
    )
    def _push(self) -> None:
        """
        _push runs a git push, retrying three times every 30 seconds and after a git pull --rebase
        """
        self.repo.remote().push().raise_if_error()

    def _get_remote_https_url(self) -> str:
        """
        _get_remote_https_url returns the remote URL for a repository
        """
        # pylint: disable=C0301
        if len(self.repo.remotes) != 1:
            raise RuntimeError(
                f"Repo '{self.name}' doesn't have exactly one remote. Actual number: {len(self.repo.remotes)}"
            )
        remote_ssh_url = self.repo.remotes[0].url
        repo_path = remote_ssh_url.split(':')[1].removesuffix('.git')
        return f"https://github.com/{repo_path}"

    def _get_latest_commit_url(self) -> str:
        """
        _get_latest_commit_url retrieves the latest commit SHA for the HEAD commit
        """
        latest_commit_sha = self.repo.head.object.hexsha
        return f"{self._get_remote_https_url()}/commit/{latest_commit_sha}"

    def add_commit_and_push(
            self, title: str, description: str = "", filepaths: list[str] = None
    ) -> None:
        """
        add_commit_and_push combines the add, _commit, and _push methods
        """
        if not self._diff():
            print("Git diff: no changes. No files will be committed.")
            return

        print(self._diff().replace("\n", "\r"))
        added_files = self.add(filepaths)
        print(f"Added following files: {added_files}")
        self._commit(title, description)
        self._push()
        print(f"Pushed a new commit: {self._get_latest_commit_url()}")
