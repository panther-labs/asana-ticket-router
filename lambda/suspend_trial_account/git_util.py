import json
import base64

import boto3 as boto3
from git import Repo
from git import cmd as git_cmd
from tenacity import retry, stop_after_attempt, wait_fixed

from os_util import join_paths, change_mode, run_cmd


class HostedDeploymentsGitRepo:
    def __init__(self, disk_path: str, branch_name: str):
        self.name = "hosted-deployments"
        self.branch_name = branch_name
        self.repo_url = f"git@github.com:panther-labs/hosted-deployments.git"
        self.path = join_paths(disk_path, self.name)
        self._ssh_key_path = join_paths(disk_path, 'id_rsa')
        self._known_hosts_path = join_paths(disk_path, 'known_hosts')
        self._setup_auth()
        self.repo = self._clone()
        self._setup_github_user()

    def _get_repo_ssh_key(self) -> str:
        client = boto3.client("secretsmanager")
        secret_name = f"airplane/{self.name}-deploy-key-base64"
        response = json.loads(client.get_secret_value(
            SecretId=secret_name)["SecretString"])
        secret_b64 = list(response.values())[0]
        return base64.b64decode(secret_b64).decode('ascii')

    def _setup_auth(self) -> None:
        ssh_key = self._get_repo_ssh_key()
        with open(self._ssh_key_path, "w") as fileobj:
            fileobj.write(f"{ssh_key}\n")
        change_mode(self._ssh_key_path, 0o600)
        print(f"Saved an ssh key for '{self.name}' to: {self._ssh_key_path}")
        run_cmd(f"ssh-keyscan github.com > {self._known_hosts_path}")
        print(f"Added github.com to known hosts at: {self._known_hosts_path}")

    def _clone(self) -> Repo:
        print(f"Cloning repo to: {self.path}")
        return Repo.clone_from(
            url=self.repo_url,
            branch=self.branch_name,
            to_path=self.path,
            env={"GIT_SSH_COMMAND": f"ssh -o UserKnownHostsFile={self._known_hosts_path} -i {self._ssh_key_path}"}
        )

    def _setup_github_user(self):
        git_config = self.repo.config_writer()
        git_config.set_value(
            "user", "email", "github-service-account@runpanther.io")
        git_config.set_value("user", "name", "panther-bot")
        git_config.release()

    def _diff(self) -> str:
        return self.repo.git.diff()

    def _add(self, filepaths: list[str] = None) -> str:
        if not filepaths:
            filepaths = [self.path]
        return self.repo.index.add(filepaths)

    def _commit(self, title: str, description: str = "") -> None:
        if description:
            title = f"{title}\n\n{description}"
        self.repo.index.commit(message=title)

    @staticmethod
    def _pull_rebase():
        print("Running 'git pull --rebase'")
        git_cmd.Git().pull('--rebase')

    @retry(wait=wait_fixed(30), stop=stop_after_attempt(3), after=lambda _: HostedDeploymentsGitRepo._pull_rebase(), reraise=True)
    def _push(self) -> None:
        self.repo.remote().push().raise_if_error()

    def _get_remote_https_url(self):
        if len(self.repo.remotes) != 1:
            raise RuntimeError(
                f"Repo '{self.name}' doesn't have exactly one remote. Actual number: {len(self.repo.remotes)}")
        remote_ssh_url = self.repo.remotes[0].url
        repo_path = remote_ssh_url.split(':')[1].removesuffix('.git')
        return f"https://github.com/{repo_path}"

    def _get_latest_commit_url(self):
        latest_commit_sha = self.repo.head.object.hexsha
        return f"{self._get_remote_https_url()}/commit/{latest_commit_sha}"

    def add_commit_and_push(self, title: str, description: str = "", filepaths: list[str] = None) -> None:
        if not self._diff():
            print("Git diff: no changes. No files will be committed.")
            return

        print(self._diff().replace("\n", "\r"))
        added_files = self._add(filepaths)
        print(f"Added following files: {added_files}")
        self._commit(title, description)
        self._push()
        print(f"Pushed a new commit: {self._get_latest_commit_url()}")
