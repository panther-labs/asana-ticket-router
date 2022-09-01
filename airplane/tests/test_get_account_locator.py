from dataclasses import asdict
from unittest import mock

import pytest

from snowflake_tasks.account_locator.get_account_locator import __name__, AirplaneParams, main

ap_params = AirplaneParams(fairytale_name="tuscan-beagle")
params = asdict(ap_params)


class TestAccountLocatorRetriever:

    @pytest.fixture(scope="function", autouse=True)
    def setup_mocks(self, request):
        patch = mock.patch(f"{__name__}.AccountLocatorRetriever.get_sf_results")
        self.sf_results_mock = patch.start()
        request.addfinalizer(patch.stop)

    def set_results(self, results):
        self.sf_results_mock.return_value = results

    def test_too_many_results_fails(self):
        self.set_results([{"account_locator": "12345"}, {"account_locator": "67890"}])
        with pytest.raises(RuntimeError):
            main(params)

    def test_too_few_results_fails(self):
        self.set_results([])
        with pytest.raises(RuntimeError):
            main(params)

    def test_successful_retrieval(self):
        locator = "12345"
        self.set_results([{"account_locator": locator}])
        assert main(params) == {"account_locator": locator}
