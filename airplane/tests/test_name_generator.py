import pytest
from unittest import mock

from operations.name_generator.name_generator import NameGenerator
from v2.exceptions import FairytaleNameAlreadyInUseException


@pytest.fixture(scope="function", autouse=True)
@mock.patch("pyshared.dynamo_db.DynamoDbSearch")
def validator(mock_ddb_search):
    mock_ddb_search = mock_ddb_search.return_value
    validator = mock.MagicMock()
    validator.ddb_search = mock_ddb_search
    validator.ddb_search.get_query_item.return_value = {}
    validator.active_domain_names = ["used.runpanther.net", "inuse.runpanther.net", "exists.runpanther.net"]
    return validator


def get_defaulted_params():
    return {
        "fairytale_name": "",
        "account_name": "mock-account-name",
        "deploy_group": "NOT_TRIAL",
        "customer_domain": ""
    }


def get_name_generator(params, validator):
    generator = NameGenerator(params)
    generator.validator = validator
    return generator


@pytest.fixture(scope="function", autouse=True)
@mock.patch("pyshared.dynamo_db.DynamoDbSearch")
def validator(mock_ddb_search):
    mock_ddb_search = mock_ddb_search.return_value
    validator = mock.MagicMock()
    validator.ddb_search = mock_ddb_search
    validator.ddb_search.get_query_item.return_value = {}
    validator.active_domain_names = ["used.runpanther.net", "inuse.runpanther.net", "exists.runpanther.net"]
    return validator


class TestNameGenerator:

    @staticmethod
    def test_generate_fairytale_and_domain_names(validator):
        names = get_name_generator(get_defaulted_params(), validator).main()
        assert names["fairytale_name"] is not None
        assert names["customer_domain"] == "mock-account-name.runpanther.net"

    @staticmethod
    def test_fairytale_passed_in_and_domain_name_generated_for_non_trial(validator):
        params = get_defaulted_params()
        params["fairytale_name"] = "mock-fairytale"
        names = get_name_generator(params, validator).main()
        assert names["fairytale_name"] is not None
        assert params["fairytale_name"] == names["fairytale_name"]
        assert names["customer_domain"] == "mock-account-name.runpanther.net"

    @staticmethod
    def test_fairytale_passed_in_and_domain_name_generated_for_trial(validator):
        params = get_defaulted_params()
        params["fairytale_name"] = "mock-fairytale"
        params["deploy_group"] = "T"
        names = get_name_generator(params, validator).main()
        assert names["fairytale_name"] is not None
        assert params["fairytale_name"] == names["fairytale_name"]
        assert names["customer_domain"] == f"{params['fairytale_name']}.runpanther.net"

    @staticmethod
    def test_generate_fairytale_and_domain_names_for_trial_accounts(validator):
        params = get_defaulted_params()
        params["deploy_group"] = "T"
        names = get_name_generator(params, validator).main()
        assert names["fairytale_name"] is not None
        assert names["customer_domain"] == f"{names['fairytale_name']}.runpanther.net"

    @staticmethod
    def test_custom_domain_passed_in_for_trial_account_fails(validator):
        params = get_defaulted_params()
        params["deploy_group"] = "T"
        params["customer_domain"] = "custom.runpanther.net"
        with pytest.raises(ValueError):
            get_name_generator(params, validator).main()

    @staticmethod
    def test_custom_domain_passed_in_for_non_trial_succeeds(validator):
        params = get_defaulted_params()
        params["customer_domain"] = "custom"
        names = get_name_generator(params, validator).main()
        assert names["fairytale_name"] is not None
        assert names["customer_domain"] == "custom.runpanther.net"

    @staticmethod
    def test_fairytale_in_use_create_new_one_for_non_trial(validator):
        params = get_defaulted_params()
        validator.run_validation.side_effect = [FairytaleNameAlreadyInUseException, lambda *args, **kwargs: None]
        names = get_name_generator(params, validator).main()
        assert names["fairytale_name"] is not None
        assert validator.run_validation.call_count == 2

    @staticmethod
    def test_fairytale_in_use_create_new_one_with_domain_as_well_for_trial(validator):
        params = get_defaulted_params()
        params["deploy_group"] = "T"
        validator.run_validation.side_effect = [FairytaleNameAlreadyInUseException, lambda *args, **kwargs: None]
        names = get_name_generator(params, validator).main()
        assert names["fairytale_name"] is not None
        assert names["fairytale_name"] in names["customer_domain"]
        assert validator.run_validation.call_count == 2
