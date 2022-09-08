from dataclasses import asdict
from unittest import mock

import pytest

from snowflake_tasks.account_locator.get_account_locator import __name__, AirplaneParams, main

ap_params = AirplaneParams(fairytale_name="tuscan-beagle", send_slack_msg=False)
params = asdict(ap_params)
ap_params_slack = AirplaneParams(fairytale_name="tuscan-beagle", send_slack_msg=True)
params_slack = asdict(ap_params_slack)


class TestAccountLocatorRetriever:

    @pytest.fixture(scope="function", autouse=True)
    def setup_mocks(self, request):
        sf_results_patch = mock.patch(f"{__name__}.AccountLocatorRetriever.get_sf_results")
        send_slack_patch = mock.patch(f"{__name__}.AccountLocatorRetriever.send_slack_message")
        self.sf_results_mock = sf_results_patch.start()
        self.send_slack_mock = send_slack_patch.start()
        request.addfinalizer(sf_results_patch.stop)
        request.addfinalizer(send_slack_patch.stop)

    def set_results(self, results):
        self.sf_results_mock.return_value = results

    def get_sent_slack_msg(self):
        return self.send_slack_mock.call_args.kwargs["message"]

    def test_one_locator_no_slack_messages(self):
        locator = "12345"
        self.set_results([{"account_locator": locator}])
        main(params)
        assert self.send_slack_mock.call_count == 0

    def test_slack_msg_no_locators(self):
        self.set_results([])
        assert main(params_slack) == {"account_locators": []}
        assert "No locators" in self.get_sent_slack_msg()

    def test_slack_msg_one_locator(self):
        locator = "12345"
        self.set_results([{"account_locator": locator}])
        assert main(params_slack) == {"account_locators": [locator]}
        # Assert a link to documentation is in the message
        assert "notion" in self.get_sent_slack_msg()

    def test_slack_msg_multiple_locators(self):
        self.set_results([{"account_locator": "12345"}, {"account_locator": "67890"}])
        return_val = main(params_slack)
        assert isinstance(return_val["account_locators"], list)
        assert len(return_val["account_locators"]) > 1
        assert "Multiple" in self.get_sent_slack_msg()
