from dataclasses import asdict
from unittest import mock

import pytest

from operations.deprovisions.change_deploy_group_to_hold.change_deploy_group_to_hold import __name__ as mod_name, \
    AirplaneParams, main
from pyshared.git_ops import __name__ as git_ops_mod_name

ap_params = AirplaneParams(fairytale_name="tuscan-beagle", organization="hosted")
params = asdict(ap_params)


class TestDeployGroupHold:

    @pytest.fixture(scope="function", autouse=True)
    def setup_mocks(self, request):
        patch = mock.patch(f"{mod_name}.change_yaml_file")
        self.change_yaml_file_mock = patch.start()
        request.addfinalizer(patch.stop)

        for patch_func, attr_name in (
            (f"{mod_name}.change_yaml_file", "change_yaml_file_mock"),
            (f"{mod_name}.generate_configs", "generate_configs_mock"),
            (f"{git_ops_mod_name}.git_clone", "git_clone_mock"),
            (f"{git_ops_mod_name}.git_add_commit_push", "git_add_commit_push_mock"),
            (f"{git_ops_mod_name}.tmp_change_dir", "change_dir_mock"),
        ):
            patch = mock.patch(patch_func)
            setattr(self, attr_name, patch.start())
            request.addfinalizer(patch.stop)

    def test_changing_group_to_hold(self):
        cfg = {"DeploymentGroup": "a"}
        self.change_yaml_file_mock.return_value.__enter__.return_value = cfg
        main(params)
        assert cfg["DeploymentGroup"] == "hold"


@pytest.mark.manual_test
def test_manual():
    main(params)
