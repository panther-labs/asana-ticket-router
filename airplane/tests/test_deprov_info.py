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

    def set_yaml_file_to_be_loaded(self, cfg):
        self.load_yaml_cfg_mock.return_value = cfg
        self.change_yaml_file_mock.return_value.__enter__.return_value = cfg

    def test_write_deprov_info(self):
        cfg = {}
        self.set_yaml_file_to_be_loaded(cfg)
        dns_time = datetime.now()
        teardown_time = datetime.now() + timedelta(hours=8)
        aws_account_id = "12345678012"
        organization = "root"
        self.deprov_info_deploy_file.write_deprov_info(
            DeprovInfo(dns_removal_time=dns_time,
                       teardown_time=teardown_time,
                       aws_account_id=aws_account_id,
                       organization=organization))
        deprov_status = cfg["DeprovisionStatus"]
        assert deprov_status["dns_removal_time"] == dns_time
        assert deprov_status["teardown_time"] == teardown_time
        assert deprov_status["aws_account_id"] == aws_account_id
        assert deprov_status["organization"] == organization

    def test_retrieve_deprov_info_with_no_deprov_info_has_none_attributes(self):
        self.set_yaml_file_to_be_loaded({"CustomerId": "my-customer"})
        deprov_info = self.deprov_info_deploy_file.retrieve_deprov_info()
        assert deprov_info.dns_removal_time is None
        assert deprov_info.teardown_time is None
        assert deprov_info.aws_account_id is None
        assert deprov_info.organization is None

    def test_retrieve_deprov_info(self):
        dns_time = datetime(year=2022, month=8, day=19, hour=16, minute=35, second=48, microsecond=297229)
        teardown_time = dns_time + timedelta(days=7)
        aws_account_id = "123456789012"
        organization = "hosted"

        self.load_yaml_cfg_mock.return_value = {
            "DeprovisionStatus": {
                "dns_removal_time": dns_time,
                "teardown_time": teardown_time,
                "aws_account_id": aws_account_id,
                "organization": organization
            }
        }
        deprov_info = self.deprov_info_deploy_file.retrieve_deprov_info()
        assert deprov_info.dns_removal_time == dns_time
        assert deprov_info.teardown_time == teardown_time
        assert deprov_info.aws_account_id == aws_account_id
        assert deprov_info.organization == organization

    def test_dns_time_existence(self):
        cfg = {"DeprovisionStatus": {"teardown_time": datetime.now()}}
        self.set_yaml_file_to_be_loaded(cfg)
        assert self.deprov_info_deploy_file.dns_removed()
        cfg["DeprovisionStatus"]["dns_removal_time"] = datetime.now()
        assert not self.deprov_info_deploy_file.dns_removed()

    def test_remove_dns_time_deprov_info_does_not_exist(self):
        self.set_yaml_file_to_be_loaded({})
        # Make sure this does not raise an exception
        self.deprov_info_deploy_file.remove_dns_time()

    def test_remove_dns_time(self):
        cfg = {"DeprovisionStatus": {"dns_removal_time": datetime.now()}}
        self.set_yaml_file_to_be_loaded(cfg)
        self.deprov_info_deploy_file.remove_dns_time()
        assert "dns_removal_time" not in cfg["DeprovisionStatus"]

    def test_get_deprov_region_does_not_exist_raises_key_error(self):
        self.set_yaml_file_to_be_loaded({})
        with pytest.raises(KeyError):
            self.deprov_info_deploy_file.get_deprov_region()

    def test_get_deprov_region(self):
        region = "us-east-1"
        self.set_yaml_file_to_be_loaded({"CustomerRegion": region})
        assert self.deprov_info_deploy_file.get_deprov_region() == region
