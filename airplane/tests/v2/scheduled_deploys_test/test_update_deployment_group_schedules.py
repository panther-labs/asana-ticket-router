import re

from tests.v2.scheduled_deploys_test.shared import *
from v2.consts.deployment_groups import HostedDeploymentGroup
from v2.tasks.scheduled_deploys.update_deployment_group_schedules.update_deployment_group_schedules import \
    UpdateDeploymentGroupSchedules


class TestUpdateDeploymentGroupSchedules:
    _TASK = UpdateDeploymentGroupSchedules(is_dry_run=True)

    @staticmethod
    def get_params(repo_path: pathlib.Path, version: str, params_to_update: dict) -> dict:
        params = {"hosted_deployments_path": repo_path, "deployment_version": version}
        params.update(params_to_update)
        return params

    def test_happy_path(self, hosted_deployments_repo, base_version, valid_new_version, valid_date, valid_time):
        deployment_group_files = {}
        for group in HostedDeploymentGroup.get_values():
            deployment_group_files[group] = read_deployment_group_file(hosted_deployments_repo, group)
        params = self.get_params(
            hosted_deployments_repo, valid_new_version, {
                "group_a_deployment_date": valid_date,
                "group_a_deployment_time": valid_time,
                "group_cpaas_deployment_date": valid_date,
                "group_cpaas_deployment_time": valid_time
            })

        self._TASK.run(params)

        # Groups A and CPaaS deployment schedules are updated
        updated_groups = [HostedDeploymentGroup.A, HostedDeploymentGroup.CPAAS]
        for group in updated_groups:
            assert_group_was_updated(hosted_deployments_repo, group, deployment_group_files[group])

        # Remaining group schedules are not updated
        not_updated_groups = set(HostedDeploymentGroup.get_values()) - set(updated_groups)
        for group in not_updated_groups:
            assert_group_was_not_updated(hosted_deployments_repo, group, deployment_group_files[group])

    def test_happy_path_without_v_prefix(self, hosted_deployments_repo, base_version,
                                         valid_new_version_without_v_prefix, valid_date, valid_time):
        deployment_group_files = {}
        for group in HostedDeploymentGroup.get_values():
            deployment_group_files[group] = read_deployment_group_file(hosted_deployments_repo, group)
        params = self.get_params(
            hosted_deployments_repo, valid_new_version_without_v_prefix, {
                "group_a_deployment_date": valid_date,
                "group_a_deployment_time": valid_time,
                "group_cpaas_deployment_date": valid_date,
                "group_cpaas_deployment_time": valid_time
            })
        self._TASK.run(params)

        # Groups A and CPaaS deployment schedules are updated
        updated_groups = [HostedDeploymentGroup.A, HostedDeploymentGroup.CPAAS]
        for group in updated_groups:
            assert_group_was_updated(hosted_deployments_repo, group, deployment_group_files[group])

        # Remaining group schedules are not updated
        not_updated_groups = set(HostedDeploymentGroup.get_values()) - set(updated_groups)
        for group in not_updated_groups:
            assert_group_was_not_updated(hosted_deployments_repo, group, deployment_group_files[group])

    def test_deployment_time_now(self, hosted_deployments_repo, base_version, valid_new_version, valid_date, now):
        deployment_group_files = {}
        for group in HostedDeploymentGroup.get_values():
            deployment_group_files[group] = read_deployment_group_file(hosted_deployments_repo, group)
        params = self.get_params(hosted_deployments_repo, valid_new_version, {
            "group_a_deployment_date": valid_date,
            "group_a_deployment_time": now,
        })

        self._TASK.run(params)

        # Group A deployment schedule is updated
        updated_groups = [HostedDeploymentGroup.A]
        for group in updated_groups:
            assert_group_was_updated(hosted_deployments_repo, group, deployment_group_files[group])

        # Remaining group schedules are not updated
        not_updated_groups = set(HostedDeploymentGroup.get_values()) - set(updated_groups)
        for group in not_updated_groups:
            assert_group_was_not_updated(hosted_deployments_repo, group, deployment_group_files[group])

    def test_past_deployment_time(self, hosted_deployments_repo, base_version, valid_new_version, valid_date,
                                  past_time):
        a_cfg = read_deployment_group_file(hosted_deployments_repo, HostedDeploymentGroup.A)
        params = self.get_params(hosted_deployments_repo, valid_new_version, {
            "group_a_deployment_date": valid_date,
            "group_a_deployment_time": past_time
        })

        # Expected exception is raised
        expected_error_msg = f"Group '{HostedDeploymentGroup.A}': {valid_date} {past_time} is a past time."
        with pytest.raises(AttributeError, match=re.escape(expected_error_msg)):
            self._TASK.run(params)

        # Group A deployment schedule was not updated
        assert_group_was_not_updated(hosted_deployments_repo, HostedDeploymentGroup.A, a_cfg)

    def test_downgrade(self, hosted_deployments_repo, base_version, downgrade_version, valid_date, valid_time):
        a_cfg = read_deployment_group_file(hosted_deployments_repo, HostedDeploymentGroup.A)
        params = self.get_params(hosted_deployments_repo, downgrade_version, {
            "group_a_deployment_date": valid_date,
            "group_a_deployment_time": valid_time
        })

        # Expected exception is raised
        expected_error_msg = f"Group '{HostedDeploymentGroup.A}': new version '{downgrade_version}' is not a valid bump from '{base_version}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A deployment schedule was not updated
        assert_group_was_not_updated(hosted_deployments_repo, HostedDeploymentGroup.A, a_cfg)

    def test_invalid_bump(self, hosted_deployments_repo, base_version, invalid_bump, valid_date, valid_time):
        a_cfg = read_deployment_group_file(hosted_deployments_repo, HostedDeploymentGroup.A)
        params = self.get_params(hosted_deployments_repo, invalid_bump, {
            "group_a_deployment_date": valid_date,
            "group_a_deployment_time": valid_time
        })

        # Expected exception is raised
        expected_error_msg = f"Group '{HostedDeploymentGroup.A}': new version '{invalid_bump}' is not a valid bump from '{base_version}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A deployment schedule was not updated
        assert_group_was_not_updated(hosted_deployments_repo, HostedDeploymentGroup.A, a_cfg)

    def test_update_to_same_version(self, hosted_deployments_repo, base_version, valid_date, valid_time):
        a_cfg = read_deployment_group_file(hosted_deployments_repo, HostedDeploymentGroup.A)
        params = self.get_params(hosted_deployments_repo, base_version, {
            "group_a_deployment_date": valid_date,
            "group_a_deployment_time": valid_time
        })

        # Expected exception is raised
        expected_error_msg = f"Group '{HostedDeploymentGroup.A}': new version '{base_version}' is not a valid bump from '{base_version}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A deployment schedule was not updated
        assert_group_was_not_updated(hosted_deployments_repo, HostedDeploymentGroup.A, a_cfg)

    def test_missing_deployment_time(self, hosted_deployments_repo, base_version, valid_new_version, valid_date):
        a_cfg = read_deployment_group_file(hosted_deployments_repo, HostedDeploymentGroup.A)
        params = self.get_params(hosted_deployments_repo, valid_new_version, {"group_a_deployment_date": valid_date})

        # Expected exception is raised
        expected_error_msg = f"Missing deployment date or time for deployment group '{HostedDeploymentGroup.A}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A deployment schedule was not updated
        assert_group_was_not_updated(hosted_deployments_repo, HostedDeploymentGroup.A, a_cfg)

    def test_missing_deployment_date(self, hosted_deployments_repo, base_version, valid_new_version, valid_time):
        a_cfg = read_deployment_group_file(hosted_deployments_repo, HostedDeploymentGroup.A)
        params = self.get_params(hosted_deployments_repo, valid_new_version, {"group_a_deployment_time": valid_time})

        # Expected exception is raised
        expected_error_msg = f"Missing deployment date or time for deployment group '{HostedDeploymentGroup.A}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A deployment schedule was not updated
        assert_group_was_not_updated(hosted_deployments_repo, HostedDeploymentGroup.A, a_cfg)
