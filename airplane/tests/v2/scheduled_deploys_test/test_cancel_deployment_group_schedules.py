from tests.v2.scheduled_deploys_test.shared import *
from v2.consts.deployment_groups import HostedDeploymentGroup
from v2.tasks.scheduled_deploys.cancel_deployment_group_schedules.cancel_deployment_group_schedules import \
    CancelDeploymentGroupSchedules


class TestUpdateDeploymentGroups:
    _TASK = CancelDeploymentGroupSchedules(is_dry_run=True)

    @staticmethod
    def _mock_deployment_files(repo_path: pathlib.Path, version: str, deployment_time: str):
        deployment_group_files = {}
        for group in HostedDeploymentGroup.get_values():
            add_group_deployment_schedule(repo_path, group, version, deployment_time)
            deployment_group_files[group] = read_deployment_group_file(repo_path, group)
        return deployment_group_files

    @staticmethod
    def get_params(repo_path: pathlib.Path, params_to_update: dict) -> dict:
        params = {"hosted_deployments_path": repo_path, "all_groups": False, "group_cpaas": False}
        for group_letter in HostedDeploymentGroup.get_values():
            params[f"group_{group_letter}"] = False
        params.update(params_to_update)
        return params

    def test_cancel_one(self, hosted_deployments_repo, valid_new_version, valid_datetime):
        deployment_files = self._mock_deployment_files(hosted_deployments_repo, valid_new_version, valid_datetime)
        params = self.get_params(hosted_deployments_repo, {"group_a": True})

        self._TASK.run(params)

        # Group A schedule is removed
        assert_group_was_updated(hosted_deployments_repo, HostedDeploymentGroup.A,
                                 deployment_files[HostedDeploymentGroup.A])

        # Remaining group files are not updated
        not_updated_groups = set(HostedDeploymentGroup.get_values()) - set(HostedDeploymentGroup.A)
        for group in not_updated_groups:
            assert_group_was_not_updated(hosted_deployments_repo, group, deployment_files[group])

    def test_cancel_all(self, hosted_deployments_repo, valid_new_version, valid_datetime):
        deployment_files = self._mock_deployment_files(hosted_deployments_repo, valid_new_version, valid_datetime)
        params = self.get_params(hosted_deployments_repo, {"all_groups": True})

        self._TASK.run(params)

        # All group schedules are removed
        for group in HostedDeploymentGroup.get_values():
            assert_group_was_updated(hosted_deployments_repo, group, deployment_files[group])

    def test_cancel_none(self, hosted_deployments_repo, valid_new_version, valid_datetime):
        params = self.get_params(hosted_deployments_repo, {})

        expected_error_msg = "No deployment schedules found for requested groups: set()"
        with pytest.raises(ValueError, match=expected_error_msg):
            self._TASK.run(params)

    def test_cancel_not_scheduled(self, hosted_deployments_repo, valid_new_version, valid_datetime):
        params = self.get_params(hosted_deployments_repo, {"group_c": True})

        expected_error_msg = "No deployment schedules found for requested groups: {'c'}"
        with pytest.raises(ValueError, match=expected_error_msg):
            self._TASK.run(params)
