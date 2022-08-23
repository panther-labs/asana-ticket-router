from datetime import datetime, timedelta
import pytest
from unittest import mock

from pyshared.deprov_info import __name__ as mod_name, DeprovInfo, DeprovInfoDeployFile


class TestDeprovInfo:

    @pytest.fixture(scope="function", autouse=True)
    def setup_mocks(self, request):
        mock_attrs = (f"change_yaml_file", "change_yaml_file_mock"), (f"load_yaml_cfg", "load_yaml_cfg_mock")
        for patch_func, attr_name in mock_attrs:
            patch = mock.patch(f"{mod_name}.{patch_func}")
            setattr(self, attr_name, patch.start())
            request.addfinalizer(patch.stop)
        self.deprov_info_deploy_file = DeprovInfoDeployFile("filepath-not-used")

    def test_write_deprov_info(self):
        cfg = {}
        self.change_yaml_file_mock.return_value.__enter__.return_value = cfg
        dns_time = datetime.now()
        teardown_time = datetime.now() + timedelta(hours=8)
        self.deprov_info_deploy_file.write_deprov_info(
            DeprovInfo(dns_removal_time=dns_time, teardown_time=teardown_time))
        deprov_status = cfg["DeprovisionStatus"]
        assert deprov_status["dns_removal_time"] == dns_time
        assert deprov_status["teardown_time"] == teardown_time

    def test_retrieve_deprov_info_with_no_deprov_info_has_none_for_delete_times(self):
        self.load_yaml_cfg_mock.return_value = {"CustomerId": "my-customer"}
        deprov_info = self.deprov_info_deploy_file.retrieve_deprov_info()
        assert deprov_info.dns_removal_time is None
        assert deprov_info.teardown_time is None

    def test_retrieve_deprov_info(self):
        dns_time = datetime(year=2022, month=8, day=19, hour=16, minute=35, second=48, microsecond=297229)
        teardown_time = dns_time + timedelta(days=7)

        self.load_yaml_cfg_mock.return_value = {
            "DeprovisionStatus": {
                "dns_removal_time": dns_time,
                "teardown_time": teardown_time
            }
        }
        deprov_info = self.deprov_info_deploy_file.retrieve_deprov_info()
        assert deprov_info.dns_removal_time == dns_time
        assert deprov_info.teardown_time == teardown_time
