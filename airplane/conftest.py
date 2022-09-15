import logging
import os
from unittest import mock

import pytest

# Required before imports create logger with a separate level
os.environ["LOG_LEVEL"] = os.getenv("LOG_LEVEL", str(logging.ERROR))

from v2.consts.airplane_env import AirplaneEnv
from v2.pyshared.airplane_logger import logger


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


@pytest.fixture(scope="session")
def airplane_session_id():
    return "123"


@pytest.fixture(scope="session")
def airplane_run_id():
    return "234"


@pytest.fixture(scope="session", autouse=True)
def manual_test_suite_setup(manual_test_run, request, airplane_session_id):
    if not manual_test_run:
        return
    _common_test_setup(request, airplane_session_id)
    local_env = _import_local_env()
    for repo_name in ("hosted-aws-management", "hosted-deployments", "panther-enterprise", "staging-deployments"):
        os.environ[repo_name] = getattr(local_env, repo_name, os.path.join(local_env.repos_parent_dir, repo_name))


@pytest.fixture(scope="session", autouse=True)
def unit_test_suite_setup(manual_test_run, request, airplane_session_id, airplane_run_id):
    if manual_test_run:
        return

    _common_test_setup(request, airplane_session_id)
    AirplaneEnv.AIRPLANE_RUN_ID = airplane_run_id
    AirplaneEnv.AIRPLANE_RUNNER_EMAIL = "unit-test-user@panther.io"


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


def _common_test_setup(request, airplane_session_id):
    for patch_obj_str in ("pyshared.airplane_utils.AirplaneTask.send_slack_message",
                          "v2.task_models.airplane_task.AirplaneTask.send_slack_message"):
        patch_obj = mock.patch(patch_obj_str)
        patch_obj.start()
        request.addfinalizer(patch_obj.stop)
    AirplaneEnv.AIRPLANE_SESSION_ID = airplane_session_id
