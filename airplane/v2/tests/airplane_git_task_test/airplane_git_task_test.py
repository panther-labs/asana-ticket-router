from v2.consts.github_repos import GithubRepo
from v2.pyshared.airplane_logger import logger
from v2.pyshared.os_util import tmp_change_dir, write_to_file, get_cwd, join_paths
from v2.task_models.airplane_git_task import AirplaneGitTask


class AirplaneGitTaskTest(AirplaneGitTask):

    def run(self, params: dict) -> None:
        for repo in GithubRepo.get_values():
            repo_abs_path = self.clone_repo_or_get_local(repo_name=repo)
            logger.info(f"Cloned repo {repo} at {repo_abs_path}")

            with tmp_change_dir(repo_abs_path):
                # Empty git diff - will not be committed
                self.git_add_commit_and_push(title="EMPTY GIT DIFF")

                # Update a file - will not be committed because of a dry_run
                readme_path = join_paths(get_cwd(), "README.md")
                write_to_file(filepath=readme_path, text=" ", is_append=True)
                self.git_add_commit_and_push(title="DRY RUN - WILL NOT BE COMMITTED")


def main(params: dict):
    AirplaneGitTaskTest(is_dry_run=True).run(params)
