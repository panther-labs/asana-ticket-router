from unittest import mock

from tests.v2.scheduled_deploys_test.shared import *
from v2.exceptions import UnpublishedPantherVersion
from v2.tasks.scheduled_deploys.scheduled_group_deploy.scheduled_group_deploy import ScheduledGroupDeploy


@pytest.fixture(scope="function", autouse=True)
def version_published(manual_test_run):
    if manual_test_run:
        yield None
    else:
        with mock.patch("v2.tasks.scheduled_deploys.scheduled_group_deploy.scheduled_group_deploy."
                        "is_version_published") as mock_version_published:
            mock_version_published.return_value = True
            yield mock_version_published


class TestUpdateDeploymentGroupSchedules:
    _TASK = ScheduledGroupDeploy(is_dry_run=True)

    @staticmethod
    def _mock_deployment_file(repo_path: pathlib.Path, group: str, version: str,
                              deployment_time: str) -> ruamel.yaml.CommentedMap:
        add_group_deployment_schedule(repo_path, group, version, deployment_time)
        return read_deployment_group_file(repo_path, group)

    @staticmethod
    def _assert_group_was_deployed(repo_path: pathlib.Path, group_cfg: ruamel.yaml.CommentedMap, group: str):
        new_group_cfg = read_deployment_group_file(repo_path, group)
        assert is_deployment_file_updated(old=group_cfg, new=new_group_cfg), \
            f"Group '{group}' deployment file was expected to be updated."
        assert is_deployment_schedule_removed(repo_path, group), \
            f"Group '{group}' deployment schedule was expected to be removed."

    @staticmethod
    def _assert_group_was_not_deployed(repo_path: pathlib.Path, group_cfg: ruamel.yaml.CommentedMap, group: str):
        new_group_cfg = read_deployment_group_file(repo_path, group)
        assert not is_deployment_file_updated(old=group_cfg, new=new_group_cfg), \
            f"Group '{group}' deployment file was expected to not be updated."
        assert not is_deployment_schedule_removed(repo_path, group), \
            f"Group '{group}' deployment schedule was expected to not be removed."

    def test_no_due_deployments(self, hosted_deployments_repo, valid_new_version, future_datetime):
        a_cfg = self._mock_deployment_file(hosted_deployments_repo, HostedDeploymentGroup.A, valid_new_version,
                                           future_datetime)
        params = {"hosted_deployments_path": hosted_deployments_repo}

        self._TASK.run(params)

        # Group A was not deployed and still contains the deployment schedule
        self._assert_group_was_not_deployed(hosted_deployments_repo, a_cfg, HostedDeploymentGroup.A)

    def test_due_deployments(self, hosted_deployments_repo, valid_new_version, future_datetime, past_datetime):
        a_cfg = self._mock_deployment_file(hosted_deployments_repo, HostedDeploymentGroup.A, valid_new_version,
                                           future_datetime)
        c_cfg = self._mock_deployment_file(hosted_deployments_repo, HostedDeploymentGroup.C, valid_new_version,
                                           past_datetime)
        params = {"hosted_deployments_path": hosted_deployments_repo}

        self._TASK.run(params)

        # Group A was not deployed and still contains the deployment schedule
        self._assert_group_was_not_deployed(hosted_deployments_repo, a_cfg, HostedDeploymentGroup.A)
        # Group C was deployed and deployment schedule removed
        self._assert_group_was_deployed(hosted_deployments_repo, c_cfg, HostedDeploymentGroup.C)

    def test_invalid_bump_deployment(self, hosted_deployments_repo, base_version, invalid_bump, past_datetime):
        a_cfg = self._mock_deployment_file(hosted_deployments_repo, HostedDeploymentGroup.A, invalid_bump,
                                           past_datetime)
        params = {"hosted_deployments_path": hosted_deployments_repo}

        expected_error_msg = f"Group '{HostedDeploymentGroup.A}': new version '{invalid_bump}' is not a valid bump from '{base_version}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A was not deployed and still contains the deployment schedule
        self._assert_group_was_not_deployed(hosted_deployments_repo, a_cfg, HostedDeploymentGroup.A)

    def test_same_version_deployment(self, hosted_deployments_repo, base_version, past_datetime):
        a_cfg = self._mock_deployment_file(hosted_deployments_repo, HostedDeploymentGroup.A, base_version,
                                           past_datetime)
        params = {"hosted_deployments_path": hosted_deployments_repo}

        expected_error_msg = f"Group '{HostedDeploymentGroup.A}': new version '{base_version}' is not a valid bump from '{base_version}'."
        with pytest.raises(AttributeError, match=expected_error_msg):
            self._TASK.run(params)

        # Group A was not deployed and still contains the deployment schedule
        self._assert_group_was_not_deployed(hosted_deployments_repo, a_cfg, HostedDeploymentGroup.A)

    def test_unpublished_version_fails(self, hosted_deployments_repo, past_datetime, version_published):
        version = "v1.35.999"
        version_published.return_value = False
        self._mock_deployment_file(hosted_deployments_repo, HostedDeploymentGroup.A, version, past_datetime)
        params = {"hosted_deployments_path": hosted_deployments_repo}

        with pytest.raises(UnpublishedPantherVersion, match=version):
            self._TASK.run(params)
