from git import Repo
from git import cmd as git_cmd
from tenacity import retry, stop_after_attempt

from v2.consts.airplane_env import AirplaneEnv
from v2.consts.github_repos import GithubRepo
from v2.consts.util_scripts import UtilScript
from v2.util.cmd_runner import run_cmd
from v2.task_models.airplane_task import AirplaneTask
from v2.pyshared.aws_secrets import get_secret_value
from v2.pyshared.base64_util import b64_decode
from v2.pyshared.airplane_logger import logger
from v2.pyshared.os_util import get_cwd, join_paths, get_user_directory, write_to_file


class AirplaneGitTask(AirplaneTask):

    def __init__(self, is_dry_run: bool = False):
        """
        :param is_dry_run: Flag indicating a dry run
        """
        super().__init__(is_dry_run)
        self._setup_github_user()

    @staticmethod
    def _setup_github_user() -> None:
        """
        If executed in Airplane, pre-configure .ssh directory with empty keys and global git user.
        Otherwise, do nothing.
        :return: None
        """
        if not AirplaneEnv.is_local_env():
            run_cmd(script_name=UtilScript.SETUP_GITHUB)
        else:
            logger.warning("Skipping git user setup due to local execution.")

    @staticmethod
    def _get_repo_deploy_key(repo_name: str) -> str:
        """
        :param repo_name: Git repo within Panther organization
        :return: SSH key allowing to clone the requested repo
        """
        secret_name = GithubRepo.get_deploy_key_secret_name(repo_name)
        secret_b64 = get_secret_value(secret_name=secret_name)
        return b64_decode(secret_b64)

    @classmethod
    def _setup_repo_ssh_key(cls, repo_name: str):
        ssh_key = cls._get_repo_deploy_key(repo_name)
        ssh_key_path = join_paths(get_user_directory(), ".ssh", "id_github")
        write_to_file(filepath=ssh_key_path, text=ssh_key, is_append=False)

    @classmethod
    def _get_remote_https_url(cls):
        repo = Repo()
        repo_name = repo.working_dir.split("/")[-1]
        if len(repo.remotes) != 1:
            raise RuntimeError(
                f"Repo '{repo_name}' doesn't have exactly one remote. Actual number: {len(repo.remotes)}")
        remote_ssh_url = repo.remotes[0].url
        repo_path = remote_ssh_url.split(':')[1].removesuffix('.git')
        return f"https://github.com/{repo_path}"

    @classmethod
    def _get_latest_commit_url(cls):
        latest_commit_sha = Repo().head.object.hexsha
        return f"{cls._get_remote_https_url()}/commit/{latest_commit_sha}"

    @classmethod
    def _git_clone(cls, repo_name: str) -> str:
        """
        Run 'git clone <repo_name>' command
        :param repo_name: Git repo to clone
        :return: Absolute path of the cloned repo
        """
        cls._setup_repo_ssh_key(repo_name)
        repo_url = GithubRepo.get_repo_url(repo_name)
        repo_path = join_paths(get_cwd(), repo_name)
        Repo.clone_from(url=repo_url, to_path=repo_path)
        return repo_path

    @staticmethod
    def _git_diff() -> str:
        """
        :return: 'git diff' output
        """
        return Repo().git.diff()

    @staticmethod
    def _git_untracked_files() -> list[str]:
        """
        :return: List of names of untracked files
        """
        return Repo().untracked_files

    @staticmethod
    def _git_add(filepaths: list[str] = None) -> None:
        """
        Run 'git add <filepaths>' command
        :param filepaths: List of absolute paths of files to add. If None, use current directory - ["."]
        :return: None
        """
        if not filepaths:
            filepaths = ["."]
        Repo().git.add(filepaths)

    @staticmethod
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

    @staticmethod
    def _git_pull_rebase():
        git_cmd.Git().pull('--rebase')

    @staticmethod
    @retry(stop=stop_after_attempt(3), after=lambda _: AirplaneGitTask._git_pull_rebase(), reraise=True)
    def _git_push() -> None:
        """
        Make up to 3 attempts to run 'git push' command. Run 'git pull --rebase' after each failed attempt.
        :return: None
        """
        Repo().remote().push()

    def clone_repo_or_get_local(self, repo_name: str, local_repo_abs_path: str = None) -> str:
        """
        If executed by Airplane, clones a repo and returns its absolute path.
        If executed locally, returns the provided absolute path of the repo
        :param repo_name: Repo name to clone or get a local copy of
        :param local_repo_abs_path: Absolute path of a local copy of the repo. Required when executing task locally.
        :return: Absolute path of the repo
        """
        if AirplaneEnv.is_local_env():
            if not local_repo_abs_path:
                raise AttributeError("Repository local path is not provided")
            logger.info(f"Using the local copy of '{repo_name}' repository: {local_repo_abs_path}")
            return local_repo_abs_path
        else:
            return self._git_clone(repo_name)

    def git_add_commit_and_push(self, title: str, description: str = "", filepaths: list[str] = None) -> None:
        """
        If file changes were made, the method adds, commits, and pushes the files to a repo in a single run.
        The method must be called from within the repo directory.
        :param title: Commit title
        :param description: Commit description
        :param filepaths: Filepaths to commit
        :return: None
        """
        git_diff_output = self._git_diff()
        untracked_files = self._git_untracked_files()
        if git_diff_output:
            logger.info(f"Git diff: {git_diff_output}")
        if untracked_files:
            untracked_files_output = ""
            for untracked_file in untracked_files:
                untracked_files_output += f"{untracked_file}:\n"
                with open(untracked_file, "r") as untracked_file_stream:
                    untracked_files_output += untracked_file_stream.read()
            logger.info(f"Untracked files:\n{untracked_files_output}")
        if not (git_diff_output or untracked_files):
            logger.warning("Git diff: no changes. No files will be committed.")
            return

        if AirplaneEnv.is_local_env() or self.is_dry_run:
            logger.info("Dry run: no files will be committed.")
        else:
            self._git_add(filepaths)
            self._git_commit(title, description)
            self._git_push()
            logger.info(f"Pushed a new commit: {self._get_latest_commit_url()}")
