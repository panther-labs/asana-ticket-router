import logging
import os

# Required before imports create logger with a separate level
os.environ["LOG_LEVEL"] = str(logging.ERROR)

import pytest

from pyshared.airplane_utils import set_local_run

try:
    import local_env
except ImportError:
    repos_parent_dir = os.path.abspath("../..")
    with open("local_env.py", "w") as local_env_file:
        local_env_file.write(f"""# Common location for all Git repos
    repos_parent_dir = "{repos_parent_dir}"
    """)
    print(f"Created local environment file, setting all git repos living under the {repos_parent_dir} path.")
    print("If this is wrong, please edit local_env.py and fix that file.")
    import local_env


def _load_environ_vars():
    set_local_run()
    for repo_name in ("hosted-deployments", "staging-deployments"):
        os.environ[repo_name] = getattr(local_env, repo_name, os.path.join(local_env.repos_parent_dir, repo_name))


@pytest.fixture(scope="session", autouse=True)
def test_suite_setup():
    _load_environ_vars()


def pytest_addoption(parser):
    parser.addoption("--manual-test", action="store_true", help="Runs manual tests marked by marker @manual_test")


def pytest_runtest_setup(item):
    if item.config.getoption("--manual-test"):
        if "manual_test" not in item.keywords:
            pytest.skip("Only running manual tests as the --manual-test option was specified")
    elif 'manual_test' in item.keywords:
        pytest.skip("need --manual-test option to run this test")
