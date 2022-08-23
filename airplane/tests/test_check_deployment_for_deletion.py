from datetime import datetime, timedelta
import pytest
from unittest import mock

from operations.deprovisions.check_deployment_for_deletion.check_deployment_for_deletion import __name__ as mod_name, \
    TaskOutput, main
from pyshared.deprov_info import DeprovInfo
from pyshared.git_ops import __name__ as git_ops_mod_name

params = {}
FAIRYTALE_NAME = "hello-world"


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

    def test_no_deprov_info_returns_empty_lists(self):
        self.deprov_info_mock.return_value = DeprovInfo()
        output = self.run_main()
        assert output.dns_removal_ready == []
        assert output.teardown_ready == []

    def test_dns_ready(self):
        self.deprov_info_mock.return_value = DeprovInfo(dns_removal_time=self.before_now, teardown_time=self.after_now)
        output = self.run_main()
        assert FAIRYTALE_NAME in output.dns_removal_ready
        assert FAIRYTALE_NAME not in output.teardown_ready

    def test_teardown_ready(self):
        self.deprov_info_mock.return_value = DeprovInfo(teardown_time=self.before_now)
        output = self.run_main()
        assert FAIRYTALE_NAME not in output.dns_removal_ready
        assert FAIRYTALE_NAME in output.teardown_ready

    def test_both_ready(self):
        self.deprov_info_mock.return_value = DeprovInfo(dns_removal_time=self.before_now, teardown_time=self.before_now)
        output = self.run_main()
        assert FAIRYTALE_NAME in output.dns_removal_ready
        assert FAIRYTALE_NAME in output.teardown_ready


@pytest.mark.manual_test
def test_manual():
    print(main(params))
