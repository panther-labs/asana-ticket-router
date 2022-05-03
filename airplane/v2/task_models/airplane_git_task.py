from v2.util.cmd_runner import run_cmd
from v2.task_models.airplane_task import AirplaneTask
from v2.pyshared.aws_secrets import get_secret_value
from v2.pyshared.os_util import join_paths, get_cur_dir_abs_path
from v2.pyshared.airplane_logger import logger
from v2.consts.airplane_env import AirplaneEnv

from git import Repo


class AirplaneGitTask(AirplaneTask):

    def __init__(self, is_dry_run: bool = False):
        """
        :param is_dry_run: Flag indicating a dry run
        """
        super().__init__(is_dry_run)
        self._setup_ssh_keys()

    @staticmethod
    def _setup_ssh_keys() -> None:
        """
        Configure git ssh keys and global user if not executed locally
        :return: None
        """
        if not AirplaneEnv.is_local_env():
            run_cmd("util/setup-github")
        else:
            logger.warning("Skipping git SSH keys setup due to local execution.")

    @staticmethod
    def _get_deploy_key_base64(repo_name: str) -> str:
        """
        :param repo_name: Git repo to clone
        :return: Deploy key required to clone repositories withing Panther organization
        """
        secret_name = run_cmd(f"REPOSITORY={repo_name} get-deploy-key-secret-name").strip()
        return get_secret_value(secret_name=secret_name)

    @classmethod
    def _git_clone(cls, repo_name: str) -> str:
        """
        Run 'git clone <repo_name>' command
        :param repo_name: Git repo to clone
        :return: Absolute path of the cloned repo
        """
        deploy_key_base64 = cls._get_deploy_key_base64(repo_name)
        run_cmd(f"REPOSITORY={repo_name} DEPLOY_KEY_BASE64={deploy_key_base64} git-clone")
        return join_paths(get_cur_dir_abs_path(), repo_name)

    @staticmethod
    def _git_diff() -> None:
        """
        Logs 'git diff' output
        :return: None
        """
        git_diff = Repo().git.diff()
        if git_diff:
            logger.info(git_diff)

    @staticmethod
    def _git_add(filepaths: list[str]) -> None:
        """
        Run 'git add <filepaths>' command
        :param filepaths: List of absolute paths of files to add
        :return: None
        """
        run_cmd(f'git-add {" ".join(filepaths)}')

    @staticmethod
    def _git_commit(title: str, description: str = "") -> None:
        """
        Run 'git commit' command
        :param title: Commit title
        :param description: Commit description
        :return: None
        """
        run_cmd(f'TITLE="{title}" DESCRIPTION="{description}" git-commit')

    @staticmethod
    def _git_push() -> None:
        """
        Run 'git push' command
        :return: None
        """
        output = run_cmd(f'TEST_RUN="false" git-push')
        if output:
            logger.info(output)

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

    def git_add_commit_and_push(self, filepaths: list[str], title: str, description: str = "") -> None:
        """
        Adds, commits, and pushes files to a specified repository in a single run.
        The method must be called from within the repo directory.
        :param filepaths: Filepaths to commit
        :param title: Commit title
        :param description: Commit description
        :return: None
        """
        if self.is_dry_run or AirplaneEnv.is_local_env():
            logger.info("Dry run: the files will not be committed, running 'git diff' instead.")
            self._git_diff()
            logger.warning('Your filesystem has been changed. You may want to undo those local changes listed above.')
        else:
            self._git_add(filepaths)
            self._git_commit(title, description)
            self._git_push()
