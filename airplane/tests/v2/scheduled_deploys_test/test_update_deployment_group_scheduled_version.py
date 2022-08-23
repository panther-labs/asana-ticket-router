from tests.v2.scheduled_deploys_test.shared import *
from v2.consts.deployment_groups import HostedDeploymentGroup
from v2.tasks.scheduled_deploys.update_deployment_group_scheduled_version.update_deployment_group_scheduled_version import \
    UpdateDeploymentGroupScheduledVersion


class TestUpdateDeploymentGroups:
    _TASK = UpdateDeploymentGroupScheduledVersion(is_dry_run=True)

    @staticmethod
    def _mock_deployment_files(repo_path: pathlib.Path, version: str, deployment_time: str):
        deployment_group_files = {}
        for group in HostedDeploymentGroup.get_values():
            add_group_deployment_schedule(repo_path, group, version, deployment_time)
            deployment_group_files[group] = read_deployment_group_file(repo_path, group)
        return deployment_group_files

    @staticmethod
    def get_params(repo_path: pathlib.Path, version: str, params_to_update: dict) -> dict:
        params = {
            "hosted_deployments_path": repo_path,
            "deployment_version": version,
            "all_groups": False,
            "group_a": False,
            "group_c": False,
            "group_e": False,
            "group_g": False,
            "group_j": False,
            "group_l": False,
            "group_n": False,
            "group_p": False,
            "group_t": False,
            "group_z": False,
            "group_cpaas": False,
            "group_legacy_sf": False
        }
        params.update(params_to_update)
        return params

    def test_update_one(self, hosted_deployments_repo, base_version, valid_new_version, valid_datetime):
        deployment_files = self._mock_deployment_files(hosted_deployments_repo, base_version, valid_datetime)
        params = self.get_params(hosted_deployments_repo, valid_new_version, {"group_a": True})

        self._TASK.run(params)

        # Group A schedule was updated
        assert_group_was_updated(hosted_deployments_repo, HostedDeploymentGroup.A,
                                 deployment_files[HostedDeploymentGroup.A])

        # Remaining group files are not updated
        not_updated_groups = set(HostedDeploymentGroup.get_values()) - set(HostedDeploymentGroup.A)
        for group in not_updated_groups:
            assert_group_was_not_updated(hosted_deployments_repo, group, deployment_files[group])

    def test_update_all(self, hosted_deployments_repo, base_version, valid_new_version, valid_datetime):
        deployment_files = self._mock_deployment_files(hosted_deployments_repo, base_version, valid_datetime)
        params = self.get_params(hosted_deployments_repo, valid_new_version, {"all_groups": True})

        self._TASK.run(params)

        # All group schedules were
        for group in HostedDeploymentGroup.get_values():
            assert_group_was_updated(hosted_deployments_repo, group, deployment_files[group])

    def test_update_all_without_v_prefix(self, hosted_deployments_repo, base_version,
                                         valid_new_version_without_v_prefix, valid_datetime):
        deployment_files = self._mock_deployment_files(hosted_deployments_repo, base_version, valid_datetime)

        params = self.get_params(hosted_deployments_repo, valid_new_version_without_v_prefix, {"all_groups": True})

        self._TASK.run(params)

        # All group schedules were
        for group in HostedDeploymentGroup.get_values():
            assert_group_was_updated(hosted_deployments_repo, group, deployment_files[group])

    def test_downgrade(self, hosted_deployments_repo, base_version, downgrade_version, valid_datetime):
        deployment_files = self._mock_deployment_files(hosted_deployments_repo, base_version, valid_datetime)
        params = self.get_params(hosted_deployments_repo, downgrade_version, {"group_a": True})

        # Expected exception is raised
        expected_error_msg = f"Group '{HostedDeploymentGroup.A}': new version '{downgrade_version}' is not a valid bump from '{base_version}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A schedule was not updated
        assert_group_was_not_updated(hosted_deployments_repo, HostedDeploymentGroup.A,
                                     deployment_files[HostedDeploymentGroup.A])

    def test_update_to_same_version(self, hosted_deployments_repo, base_version, valid_datetime):
        deployment_files = self._mock_deployment_files(hosted_deployments_repo, base_version, valid_datetime)
        params = self.get_params(hosted_deployments_repo, base_version, {"group_a": True})

        # Expected exception is raised
        expected_error_msg = f"Group '{HostedDeploymentGroup.A}': new version '{base_version}' is not a valid bump from '{base_version}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A schedule was not updated
        assert_group_was_not_updated(hosted_deployments_repo, HostedDeploymentGroup.A,
                                     deployment_files[HostedDeploymentGroup.A])

    def test_update_none(self, hosted_deployments_repo, base_version, valid_new_version, valid_datetime):
        deployment_files = self._mock_deployment_files(hosted_deployments_repo, base_version, valid_datetime)
        params = self.get_params(hosted_deployments_repo, valid_new_version, {})

        expected_error_msg = "No deployment schedules were found for the requested groups. No changes will be made."
        with pytest.raises(ValueError, match=expected_error_msg):
            self._TASK.run(params)

        # All group schedules were
        for group in HostedDeploymentGroup.get_values():
            assert_group_was_not_updated(hosted_deployments_repo, group, deployment_files[group])

    def test_update_with_missing_schedule(self, hosted_deployments_repo, valid_new_version, valid_datetime):
        params = self.get_params(hosted_deployments_repo, valid_new_version, {"group_a": True})

        expected_error_msg = "No deployment schedules were found for the requested groups. No changes will be made."
        with pytest.raises(ValueError, match=expected_error_msg):
            self._TASK.run(params)
