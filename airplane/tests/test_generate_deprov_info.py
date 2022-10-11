import datetime
import pytest
from dataclasses import asdict
from unittest import mock

from operations.deprovisions import DEPROV_TZ
from operations.deprovisions.generate_deprov_info.generate_deprov_info import __name__ as mod_name, \
    main, AirplaneParams
from pyshared.deprov_info import DeprovInfo

ap_params = AirplaneParams(fairytale_name="tuscan-beagle",
                           hours_before_dns_removal=4,
                           hours_before_teardown=16,
                           org_name="hosted",
                           aws_account_id="451868014754",
                           company_display_name="Orbit",
                           domain="orbit.runpanther.net",
                           region="us-west-2")
params = asdict(ap_params)


class TestDeprovTimes:

    @pytest.fixture(scope="function", autouse=True)
    def setup_mocks(self, manual_test_run, request):
        if not manual_test_run:
            for patch_func, attr_name in (("DeprovInfoGenerator.send_slack_message", "send_slack_msg_mock"), ):
                patch = mock.patch(f"{mod_name}.{patch_func}")
                setattr(self, attr_name, patch.start())
                request.addfinalizer(patch.stop)

    def test_slack_message_contains_customer_info_and_sent_to_right_channels(self):
        main(params)
        args_index = 2
        slack_msg = self.send_slack_msg_mock.mock_calls[0][args_index]
        assert slack_msg["channel_name"] == "#eng-deployment-notifications"
        msg = slack_msg["message"]
        assert ap_params.fairytale_name in msg
        assert ap_params.aws_account_id in msg
        assert ap_params.company_display_name in msg
        assert ap_params.domain in msg

    def test_proper_teardown_times_set(self):
        now = str(datetime.datetime.now(DEPROV_TZ))
        output = DeprovInfo(**main(params))

        assert output.dns_removal_time > now
        assert output.teardown_time > now
        assert output.aws_account_id == "451868014754"
        assert output.organization == "hosted"


@pytest.mark.manual_test
def test_manual():
    main(params)
