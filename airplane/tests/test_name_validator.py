import pytest
from unittest import mock

from operations.name_generator.name_validator import NameValidator
from v2.exceptions import DomainNameAlreadyInUseException, FairytaleNameAlreadyInUseException


@pytest.fixture(scope="function", autouse=True)
@mock.patch("pyshared.dynamo_db.DynamoDbSearch")
def validator(mock_ddb_search):
    mock_ddb_search = mock_ddb_search.return_value
    validator = NameValidator()
    validator.ddb_search = mock_ddb_search
    validator.ddb_search.get_query_item.return_value = {}
    set_route53_record_found(validator, False)
    return validator


def set_route53_record_found(validator: NameValidator, found: bool):
    validator._does_route53_record_exist_with_domain_name = lambda *args, **kwargs: found


class TestNameValidator:

    @staticmethod
    def test_valid_fairytale_or_domain_name(validator):
        is_valid = validator.run_validation(domain_name="valid.runpanther.net", fairytale_name="valid-fairytale")
        assert is_valid is True

    @staticmethod
    def test_domain_name_already_in_use(validator):
        set_route53_record_found(validator, True)
        with pytest.raises(DomainNameAlreadyInUseException):
            validator.run_validation(domain_name="used.runpanther.net", fairytale_name="valid-fairytale")

    @staticmethod
    def test_fairytale_name_already_in_use(validator):
        validator.ddb_search.get_query_item.return_value = {"CustomerId": "exists-fairytale"}
        with pytest.raises(FairytaleNameAlreadyInUseException):
            validator.run_validation(domain_name="unused.runpanther.net", fairytale_name="exists-fairytale")
