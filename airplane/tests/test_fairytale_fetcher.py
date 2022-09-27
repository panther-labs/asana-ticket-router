import pytest
from unittest import mock

from operations.fairytale_fetcher.fairytale_fetcher import FairytaleFetcher
from v2.exceptions import SalesIdNotFoundException


@pytest.fixture(scope="function", autouse=True)
@mock.patch("pyshared.dynamo_db.DynamoDbSearch")
def fetcher(mock_ddb_search):
    mock_ddb_search = mock_ddb_search.return_value
    fetcher = FairytaleFetcher()
    fetcher.ddb_search = mock_ddb_search
    fetcher.ddb_search.get_query_items.return_value = {}
    return fetcher


def mocked_table_entries(entry_count):
    return [{
        'CustomerId': f'mock-fairytale{i}',
        'SalesOpportunityId': f'mock-opp-id{i}',
        'SalesCustomerId': f'mock-customer-id{i}'
    } for i in range(entry_count)]


class TestFairytaleFetcher:

    @staticmethod
    def test_valid_sales_ids(fetcher):
        fetcher.ddb_search.get_query_items.return_value = mocked_table_entries(1)
        fairytale = fetcher.main('mock-customer-id0', 'mock-opp-id0')
        assert fairytale == 'mock-fairytale0'

    @staticmethod
    def test_invalid_sales_opportunity_id(fetcher):
        fetcher.ddb_search.get_query_items.return_value = mocked_table_entries(2)
        with pytest.raises(SalesIdNotFoundException):
            fetcher.main('mock-customer-id1', 'wrong-opp-id')

    @staticmethod
    def test_invalid_sales_customer_id(fetcher):
        # This mimics the behavior of DynamoDB not returning anything for
        # invalid/non-existent SalesCustomerIds being passed
        fetcher.ddb_search.get_query_items.return_value = []
        with pytest.raises(SalesIdNotFoundException):
            fetcher.main('mock-customer-id-invalid', 'mock-opp-id0')

    @staticmethod
    def test_multiple_entries_for_single_customer_id(fetcher):
        table_entries = mocked_table_entries(2)
        table_entries.append({
            # This adds another entry that would share a SalesCustomerId
            'CustomerId': 'mock-fairytale-foo',
            'SalesOpportunityId': 'mock-opp-id-foo',
            'SalesCustomerId': 'mock-customer-id1'
        })
        fetcher.ddb_search.get_query_items.return_value = table_entries
        fairytale = fetcher.main('mock-customer-id1', 'mock-opp-id-foo')
        assert fairytale == 'mock-fairytale-foo'
