import datetime
import pytest
from dataclasses import asdict
from unittest import mock

from operations.deprovisions.mark_deployment_for_deletion.mark_deployment_for_deletion import __name__ as mod_name, \
    main, AirplaneParams, DeploymentDeletionMarker
from tests import change_airplane_env_var

ap_params = AirplaneParams(fairytale_name="tuscan-beagle",
                           hours_before_dns_removal=4,
                           hours_before_teardown=16,
                           org_name="hosted",
                           aws_account_id="451868014754",
                           company_display_name="Orbit",
                           domain="orbit.runpanther.net",
                           api_use_only=False)
params = asdict(ap_params)


class TestMarkDeploymentForDeletion:

    @pytest.fixture(scope="function", autouse=True)
    def setup_mocks(self, manual_test_run, request):
        if not manual_test_run:
            for patch_func, attr_name in (("DeprovInfoDeployFile", "deprov_info_deploy_file_mock"),
                                          ("alter_deployment_file", "alter_deployment_file_mock"),
                                          ("DeploymentDeletionMarker.send_slack_message", "send_slack_msg_mock")):
                patch = mock.patch(f"{mod_name}.{patch_func}")
                setattr(self, attr_name, patch.start())
                request.addfinalizer(patch.stop)
            self.alter_deployment_file_mock.return_value = mock.MagicMock(), None

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

    def test_must_be_part_of_a_runbook(self):
        with change_airplane_env_var("AIRPLANE_SESSION_ID", ""):
            with pytest.raises(RuntimeError):
                main(params)

    def test_proper_teardown_times_set(self):
        mock_start_time = datetime.datetime(year=2022, month=8, day=19, hour=10, minute=0, second=0)
        expected_dns_removal_time = datetime.datetime(year=2022, month=8, day=19, hour=14, minute=0, second=0)
        expected_teardown_time = datetime.datetime(year=2022, month=8, day=19, hour=18, minute=0, second=0)
        expected_aws_account_id = "111111111111"
        expected_organization = "root"
        deprov_info = DeploymentDeletionMarker.add_deprovisioning_tags(filepath="mockedout",
                                                                       dns_removal_hours=4,
                                                                       teardown_removal_hours=8,
                                                                       aws_account_id=expected_aws_account_id,
                                                                       organization=expected_organization,
                                                                       now=mock_start_time)

        assert deprov_info.dns_removal_time == expected_dns_removal_time
        assert deprov_info.teardown_time == expected_teardown_time
        assert deprov_info.aws_account_id == expected_aws_account_id
        assert deprov_info.organization == expected_organization


@pytest.mark.manual_test
def test_manual():
    main(params)
