import logging
import os

# Required before imports create logger with a separate level
os.environ["LOG_LEVEL"] = str(logging.ERROR)

import pytest

from pyshared.airplane_utils import set_local_run


def _import_local_env():
    """This function exists with imports within it to prevent creating files during unit test runs in GitHub Actions."""
    try:
        import local_env
    except ModuleNotFoundError:
        repos_parent_dir = os.path.abspath("../..")
        with open("local_env.py", "w") as local_env_file:
            local_env_file.write(f"""# Common location for all Git repos
        repos_parent_dir = "{repos_parent_dir}"
        """)
        print(f"Created local environment file, setting all git repos living under the {repos_parent_dir} path.")
        print("If this is wrong, please edit local_env.py and fix that file.")
        import local_env
    return local_env


@pytest.fixture(scope="session", autouse=True)
def manual_test_suite_run_setup(manual_test_run):
    if not manual_test_run:
        return

    local_env = _import_local_env()
    set_local_run()
    for repo_name in ("hosted-deployments", "staging-deployments"):
        os.environ[repo_name] = getattr(local_env, repo_name, os.path.join(local_env.repos_parent_dir, repo_name))


def pytest_addoption(parser):
    parser.addoption("--manual-test", action="store_true", help="Runs manual tests marked by marker @manual_test")


@pytest.fixture(scope="session")
def manual_test_run(pytestconfig):
    return pytestconfig.getoption("manual_test")


def pytest_runtest_setup(item):
    if item.config.getoption("--manual-test"):
        if "manual_test" not in item.keywords:
            pytest.skip("Only running manual tests as the --manual-test option was specified")
    elif 'manual_test' in item.keywords:
        pytest.skip("need --manual-test option to run this test")
