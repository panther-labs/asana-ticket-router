from datetime import datetime, timedelta
import pytest
from unittest import mock

from operations.deprovisions.check_deployment_for_deletion.check_deployment_for_deletion import __name__ as mod_name, \
    TaskOutput, main
from pyshared.deprov_info import DeprovInfo
from pyshared.git_ops import __name__ as git_ops_mod_name

params = {}
AWS_ACCOUNT_ID = "555555555555"
FAIRYTALE_NAME = "hello-world"
ORG = "root"


class TestCheckDeploymentForDeletion:

    @pytest.fixture(scope="function", autouse=True)
    def setup_mocks(self, manual_test_run, request):
        if not manual_test_run:
            for patch_func, attr_name in (
                (f"{mod_name}.datetime", "datetime_mock"),
                (f"{mod_name}.get_deployment_targets", "deploy_targets_mock"),
                (f"{mod_name}.DeprovInfoDeployFile", "deprov_info_deploy_file_mock"),
                (f"{git_ops_mod_name}.git_clone", "git_clone_mock"),
                (f"{git_ops_mod_name}.tmp_change_dir", "change_dir_mock"),
            ):
                patch = mock.patch(patch_func)
                setattr(self, attr_name, patch.start())
                request.addfinalizer(patch.stop)
            self.deploy_targets_mock.return_value = [f"path/to/{FAIRYTALE_NAME}.yml"]
            self.deprov_info_mock = self.deprov_info_deploy_file_mock.return_value.retrieve_deprov_info
            self.now = datetime.now()
            self.datetime_mock.now.return_value = self.now
            self.before_now = self.now - timedelta(hours=1)
            self.after_now = self.now + timedelta(hours=1)

    @staticmethod
    def run_main() -> TaskOutput:
        return TaskOutput(**main(params))

    @staticmethod
    def get_deprov_info(dns_removal_time=None, teardown_time=None) -> DeprovInfo:
        return DeprovInfo(dns_removal_time=dns_removal_time,
                          teardown_time=teardown_time,
                          aws_account_id=AWS_ACCOUNT_ID,
                          organization=ORG)

    def test_no_deprov_info_returns_no_teardown_info(self):
        self.deprov_info_mock.return_value = DeprovInfo()
        output = self.run_main()
        assert output.deprov_type == ""
        assert output.fairytale_name == ""
        assert output.org == ""

    def test_all_return_attributes_match_deprov_info(self):
        self.deprov_info_mock.return_value = self.get_deprov_info(dns_removal_time=self.before_now)
        output = self.run_main()
        assert output.aws_account_id == AWS_ACCOUNT_ID
        assert output.deprov_type == "dns"
        assert output.fairytale_name == FAIRYTALE_NAME
        assert output.org == ORG

    def test_dns_ready(self):
        self.deprov_info_mock.return_value = self.get_deprov_info(dns_removal_time=self.before_now,
                                                                  teardown_time=self.after_now)
        assert self.run_main().deprov_type == "dns"

    def test_teardown_ready(self):
        self.deprov_info_mock.return_value = self.get_deprov_info(teardown_time=self.before_now)
        assert self.run_main().deprov_type == "teardown"

    def test_both_ready(self):
        self.deprov_info_mock.return_value = self.get_deprov_info(dns_removal_time=self.before_now,
                                                                  teardown_time=self.before_now)
        assert self.run_main().deprov_type == "dns"


@pytest.mark.manual_test
def test_manual():
    print(main(params))
