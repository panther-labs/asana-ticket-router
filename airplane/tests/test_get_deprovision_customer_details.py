import pytest

from dataclasses import asdict
from unittest import mock

from operations.deprovisions.get_deprovision_customer_details.get_deprovision_customer_details import AirplaneParams, \
    DeploymentCustomerDetails, DuplicateAwsAccountIdException, DuplicateNotionFairytaleNameException, \
    InvalidFairytaleNameException, InvalidRegionException, main
from tests.mocks.all_customer_accounts_info import MockAllCustomerAccountsInfo
from tests.mocks.deployment_metadata_table import get_metadata_table_ddb_cfg


@pytest.fixture(scope="function", autouse=True)
def mock_all_accounts_info(manual_test_run) -> MockAllCustomerAccountsInfo:
    if manual_test_run:
        yield None
    else:
        with mock.patch("operations.deprovisions.get_deprovision_customer_details.get_deprovision_customer_details."
                        "AllCustomerAccountsInfo") as mock_accounts_info:
            mock_accounts_info.return_value = MockAllCustomerAccountsInfo()
            yield mock_accounts_info.return_value


def test_invalid_fairytale_name(mock_all_accounts_info):
    with pytest.raises(InvalidFairytaleNameException):
        DeploymentCustomerDetails().run(asdict(AirplaneParams(fairytale_name="no-exist", org_name="hosted")))


def test_invalid_org_name(mock_all_accounts_info):
    mock_all_accounts_info.create_fake_customer(fairytale_name="my-customer")

    with pytest.raises(ValueError):
        DeploymentCustomerDetails().run(asdict(AirplaneParams(fairytale_name="my-customer", org_name="invalid_org")))


def test_multiple_fairytale_names_in_notion_fails(mock_all_accounts_info):
    fairytale_name = "test-account"
    mock_all_accounts_info.create_fake_customer(fairytale_name=fairytale_name)
    mock_all_accounts_info.notion_duplicates = [fairytale_name]
    with pytest.raises(DuplicateNotionFairytaleNameException, match=fairytale_name):
        DeploymentCustomerDetails().run(asdict(AirplaneParams(fairytale_name=fairytale_name, org_name="hosted")))


def test_same_aws_account_id_diff_regions_no_region_param_fails(mock_all_accounts_info):
    mock_all_accounts_info.create_fake_customer(fairytale_name="region1-customer")
    mock_all_accounts_info.create_fake_customer(fairytale_name="region2-customer",
                                                dynamo=get_metadata_table_ddb_cfg().update(
                                                    {"GithubConfiguration": {
                                                        "region": "us-east-2",
                                                    }}))

    with pytest.raises(DuplicateAwsAccountIdException, match="region2-customer"):
        DeploymentCustomerDetails().run(asdict(AirplaneParams(fairytale_name="region1-customer", org_name="hosted")))

    with pytest.raises(DuplicateAwsAccountIdException, match="region1-customer"):
        DeploymentCustomerDetails().run(asdict(AirplaneParams(fairytale_name="region2-customer", org_name="hosted")))


def test_same_aws_account_id_same_region_fails(mock_all_accounts_info):
    mock_all_accounts_info.create_fake_customer(fairytale_name="customer-1")
    mock_all_accounts_info.create_fake_customer(fairytale_name="sameregion-customer")

    with pytest.raises(DuplicateAwsAccountIdException, match="us-west-2"):
        DeploymentCustomerDetails().run(
            asdict(AirplaneParams(fairytale_name="customer-1", org_name="hosted", region="us-west-2")))


def test_invalid_region_fails(mock_all_accounts_info):
    mock_all_accounts_info.create_fake_customer(fairytale_name="uswest2-region")
    with pytest.raises(InvalidRegionException, match="us-east-2"):
        DeploymentCustomerDetails().run(
            asdict(AirplaneParams(fairytale_name="uswest2-region", org_name="hosted", region="us-east-2")))


def test_diff_regions_same_account_has_warning_in_output(mock_all_accounts_info):
    mock_all_accounts_info.create_fake_customer(fairytale_name="region-1")
    mock_all_accounts_info.create_fake_customer(fairytale_name="region-2",
                                                dynamo={
                                                    **get_metadata_table_ddb_cfg(),
                                                    **{
                                                        "GithubConfiguration": {
                                                            "CustomerRegion": "us-east-2",
                                                        }
                                                    }
                                                })

    output = DeploymentCustomerDetails().run(
        asdict(AirplaneParams(fairytale_name="region-2", org_name="hosted", region="us-east-2")))
    assert output["region"] == "us-east-2"
    assert not output["is_safe_to_close"]
    assert "multiple_accounts" in output["warnings"]


def test_happy_path(mock_all_accounts_info):
    mock_all_accounts_info.create_fake_customer(fairytale_name="happy-customer")
    output = DeploymentCustomerDetails().run(asdict(AirplaneParams(fairytale_name="happy-customer", org_name="root")))
    assert output["account_id"] == "123456789012"
    assert output["is_safe_to_close"]
    assert output["company_display_name"] == "CompanyDisplayName"
    assert output["domain"] == "companydisplayname.runpanther.net"
    assert output["region"] == "us-west-2"
    assert output["org"] == "root"
    assert output["warnings"] == {}


@pytest.mark.manual_test
def test_manual():
    # TODO: Requires adding test roles, currently doesn't work when calling via pytest
    params = AirplaneParams(fairytale_name="tangible-dinosaur", org_name="hosted")
    main(asdict(params))
