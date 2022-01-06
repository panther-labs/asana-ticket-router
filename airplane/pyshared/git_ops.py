import subprocess


def setup_github():
    """Requires the DEPLOY_KEY_BASE64 environment variable to be set in the Airplane task."""
    subprocess.run("util/setup-github")


def git_clone(repo, github_setup=False):
    if github_setup:
        setup_github()
    subprocess.run(f"REPOSITORY={repo} util/git-clone", shell=True)
    return repo
