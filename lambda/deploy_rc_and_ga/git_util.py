import os
import json
import base64

import boto3 as boto3
from git import Repo
from git import cmd as git_cmd
from tenacity import retry, stop_after_attempt, wait_fixed


def get_github_secret_name(repo_name: str) -> str or None:
    if repo_name == "hosted-deployments":
        return "airplane/hosted-deployments-deploy-key-base64"
    if repo_name == "staging-deployments":
        return "airplane/staging-deployments-deploy-key-base64"


def _get_repo_ssh_key(repo_name: str) -> str:
    client = boto3.client("secretsmanager")
    secret_name = get_github_secret_name(repo_name)
    response = json.loads(client.get_secret_value(SecretId=secret_name)["SecretString"])
    secret_b64 = list(response.values())[0]
    return base64.b64decode(secret_b64).decode('ascii')


def _setup_repo_ssh_key(target_dir: str, repo_name: str) -> None:
    ssh_key = _get_repo_ssh_key(repo_name)
    with open(f"{target_dir}/id_rsa", "w") as fileobj:
        fileobj.write(ssh_key)
    os.chmod(f"{target_dir}/id_rsa", 0o600)
    os.system("ssh-keyscan -t rsa github.com | tee /tmp/known_hosts | ssh-keygen -lf -")


def git_clone(target_dir: str, repo_name: str, branch_name: str) -> str:
    _setup_repo_ssh_key(target_dir, repo_name)
    repo_path = f"{target_dir}/{repo_name}"
    repo = Repo.clone_from(
        url=f"git@github.com:panther-labs/{repo_name}.git",
        branch=branch_name,
        to_path=repo_path,
        env={"GIT_SSH_COMMAND": f"ssh -o UserKnownHostsFile=/tmp/known_hosts -i {target_dir}/id_rsa"}
    )
    git_config = repo.config_writer()
    git_config.set_value("user", "email", "github-service-account@runpanther.io")
    git_config.set_value("user", "name", "panther-bot")
    git_config.release()
    return repo_path


def _git_diff() -> str:
    """
    :return: 'git diff' output
    """
    return Repo().git.diff()


def _git_add(filepaths: list[str] = None) -> None:
    """
    Run 'git add <filepaths>' command
    :param filepaths: List of absolute paths of files to add. If None, use current directory - ["."]
    :return: None
    """
    if not filepaths:
        filepaths = ["."]
    Repo().git.add(filepaths)


def _git_commit(title: str, description: str = "") -> None:
    """
    Run 'git commit' command
    :param title: Commit title
    :param description: Commit description
    :return: None
    """
    if description:
        title = f"{title}\n\n{description}"
    Repo().index.commit(message=title)


def _git_pull_rebase():
    print("Running 'git pull --rebase'")
    git_cmd.Git().pull('--rebase')


@retry(wait=wait_fixed(30), stop=stop_after_attempt(3), after=lambda _: _git_pull_rebase(), reraise=True)
def _git_push() -> None:
    """
    Make up to 3 attempts to run 'git push' command. Run 'git pull --rebase' after each failed attempt.
    :return: None
    """
    Repo().remote().push().raise_if_error()


def _get_remote_https_url():
    repo = Repo()
    repo_name = repo.working_dir.split("/")[-1]
    if len(repo.remotes) != 1:
        raise RuntimeError(
            f"Repo '{repo_name}' doesn't have exactly one remote. Actual number: {len(repo.remotes)}")
    remote_ssh_url = repo.remotes[0].url
    repo_path = remote_ssh_url.split(':')[1].removesuffix('.git')
    return f"https://github.com/{repo_path}"


def _get_latest_commit_url():
    latest_commit_sha = Repo().head.object.hexsha
    return f"{_get_remote_https_url()}/commit/{latest_commit_sha}"


def git_add_commit_and_push(title: str, description: str = "", filepaths: list[str] = None) -> None:
    """
    If file changes were made, the method adds, commits, and pushes the files to a repo in a single run.
    The method must be called from within the repo directory.
    :param title: Commit title
    :param description: Commit description
    :param filepaths: Filepaths to commit
    :return: None
    """
    diff = _git_diff()
    if not diff:
        print("Git diff: no changes. No files will be committed.")
        return

    print(diff.replace("\n", "\r"))
    _git_add(filepaths)
    _git_commit(title, description)
    _git_push()
    print(f"Pushed a new commit: {_get_latest_commit_url()}")
