import pytest

from unittest import mock

from operations.deployment.deployment_health_checker.deployment_health_checker import main as run_task
from tests.mocks.all_customer_accounts_info import MockAllCustomerAccountsInfo
from tests.mocks.notion_databases import MockAccountsDatabase
from v2.consts.airplane_env import AirplaneEnv

FAIRYTALE_NAME_1 = "my-customer1"
FAIRYTALE_NAME_2 = "my-customer2"
FAIRYTALE_NAME_3 = "my-customer3"
FAKE_SESSION_ID = "123"


@pytest.fixture(scope="function", autouse=True)
def setup_runbook_url():
    AirplaneEnv.AIRPLANE_SESSION_ID = FAKE_SESSION_ID


@pytest.fixture(scope="function", autouse=True)
def day_of_week() -> mock.MagicMock:
    with mock.patch("operations.deployment.deployment_health_checker.deployment_health_checker.get_day_of_week_name") \
            as mock_day_of_week:
        mock_day_of_week.return_value = "Thursday"
        yield mock_day_of_week


@pytest.fixture(scope="function", autouse=True)
def mock_all_accounts_info(manual_test_run) -> MockAllCustomerAccountsInfo:
    if manual_test_run:
        yield None
    with mock.patch("operations.deployment.deployment_health_checker.deployment_health_checker."
                    "AllCustomerAccountsInfo") as mock_accounts_info:
        accounts_info = MockAllCustomerAccountsInfo()
        for name in (FAIRYTALE_NAME_1, FAIRYTALE_NAME_2, FAIRYTALE_NAME_3):
            accounts_info.create_fake_customer(fairytale_name=name)
            accounts_info.notion_accounts[name] = MockAccountsDatabase()
            accounts_info.notion_accounts[name].Fairytale_Name = name
            accounts_info.notion_accounts[name].Actual_Version = ""
        mock_accounts_info.return_value = accounts_info
        yield mock_accounts_info.return_value


def _setup_airplane_creations(mock_all_accounts_info):
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Airplane_Creation_Link = "https://app.airplane.com"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Airplane_Creation_Completed = False
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Airplane_Creation_Link = "https://app.airplane.com"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Airplane_Creation_Completed = True
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Airplane_Creation_Link = ""
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Airplane_Creation_Completed = False


def test_unfinished_airplane_creation(mock_all_accounts_info):
    _setup_airplane_creations(mock_all_accounts_info)
    result = run_task({})

    # Creation link exists and not finished should be reported
    assert FAIRYTALE_NAME_1 in result["unfinished_airplane"]

    # Creation link exists and finished should not be reported
    assert FAIRYTALE_NAME_2 not in result["unfinished_airplane"]

    # No airplane creation link, meaning the account wasn't created via Airplane, should not be reported
    assert FAIRYTALE_NAME_3 not in result["unfinished_airplane"]


def _setup_mismatched_panther_versions(mock_all_accounts_info):
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Expected_Version = "1.2.3"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Actual_Version = "1.2.3"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Expected_Version = "1.2.3"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Actual_Version = "1.1.0"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Expected_Version = "1.2.3"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Actual_Version = ""


def test_mismatched_panther_versions(mock_all_accounts_info):
    _setup_mismatched_panther_versions(mock_all_accounts_info)
    result = run_task({})

    # Versions match, no error
    assert FAIRYTALE_NAME_1 not in result["mismatched_panther_versions"]

    # Version mismatch, error
    assert FAIRYTALE_NAME_2 in result["mismatched_panther_versions"][0]

    # No actual version does not cause error - deployment automation hasn't yet put anything in for actual version
    assert FAIRYTALE_NAME_3 not in result["mismatched_panther_versions"]


def _setup_deploy_group_inconsistency(mock_all_accounts_info):
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Deploy_Group = "a"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Deploy_Group = "l"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Deploy_Group = "z"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Actual_Version = "1.2.3"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Actual_Version = "1.2.1"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Actual_Version = "1.1.0"


def test_deploy_group_inconsistency(mock_all_accounts_info):
    _setup_deploy_group_inconsistency(mock_all_accounts_info)
    result = run_task({})

    # On a fake latest version
    assert FAIRYTALE_NAME_1 not in result["deploy_group_inconsistency"]

    # Not on latest version, but still within same minor version
    assert FAIRYTALE_NAME_2 not in result["deploy_group_inconsistency"]

    # On a previous minor version, that's a problem
    assert FAIRYTALE_NAME_3 in result["deploy_group_inconsistency"]


def _setup_only_customer_deploy_groups_are_processed(mock_all_accounts_info):
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Deploy_Group = "a"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Deploy_Group = "l"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Deploy_Group = "Internal"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Actual_Version = "5.6.7"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Actual_Version = "5.6.7"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Actual_Version = "1.1.0"


def test_only_customer_deploy_groups_are_processed(mock_all_accounts_info):
    _setup_only_customer_deploy_groups_are_processed(mock_all_accounts_info)
    result = run_task({})

    assert not result["deploy_group_inconsistency"]


def test_deploy_groups_not_processed_on_upgrade_days(mock_all_accounts_info, day_of_week):
    day_of_week.return_value = "Tuesday"
    _setup_deploy_group_inconsistency(mock_all_accounts_info)
    result = run_task({})

    assert not result["deploy_group_inconsistency"]


def _setup_latest_version(mock_all_accounts_info):
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_1].Actual_Version = "10.2.3"
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_2].Actual_Version = ""
    mock_all_accounts_info.notion_accounts[FAIRYTALE_NAME_3].Actual_Version = "2.1.2"


def test_latest_version(mock_all_accounts_info):
    _setup_latest_version(mock_all_accounts_info)
    result = run_task({})

    assert result["latest_deployed_ga_version"] == "10.2.3"


def test_happy_path():
    result = run_task({})
    assert not result["unfinished_airplane"]
    assert not result["mismatched_panther_versions"]
    assert result["runbook_url"] == f"https://app.airplane.dev/sessions/{FAKE_SESSION_ID}"
