import git
import os
import pathlib
import pytest
import ruamel

from v2.pyshared.yaml_utils import load_yaml_cfg
from v2.tasks.disable_customer_sentry_alerts.disable_customer_sentry_alerts import main, DisableCustomerSentryAlerts


@pytest.fixture
def no_cfn_params_customer() -> str:
    return "no-cfn-customer"


@pytest.fixture
def no_sentry_params_customer() -> str:
    return "no-sentry-customer"


@pytest.fixture
def sentry_params_customer() -> str:
    return "sentry-customer"


def _create_deployment_file(content: str, fairytale_name: str, parent_dir: pathlib.Path) -> None:
    file_path = parent_dir / f"{fairytale_name}.yml"
    file_path.write_text(content)


def _create_no_cfn_params_customer_file(fairytale_name: str, parent_dir: pathlib.Path) -> None:
    content = f"""
    CustomerId: {fairytale_name}
    BaseRootEmail: panther-hosted@runpanther.io
    CustomerRegion: us-west-2
    DeploymentGroup: a
    """
    _create_deployment_file(content, fairytale_name, parent_dir)


def _create_no_sentry_params_customer_file(fairytale_name: str, parent_dir: pathlib.Path) -> None:
    content = f"""
    CustomerId: {fairytale_name}
    BaseRootEmail: panther-hosted@runpanther.io
    CustomerRegion: us-west-2
    DeploymentGroup: a
    CloudFormationParameters:
      CompanyDisplayName: {fairytale_name}
      CustomDomain: {fairytale_name}.runpanther.net
      FirstUserEmail: {fairytale_name}@panther.io
      FirstUserFamilyName: Test
      FirstUserGivenName: User
      OnboardSelf: false
    """
    _create_deployment_file(content, fairytale_name, parent_dir)


def _create_sentry_customer_file(fairytale_name: str, parent_dir: pathlib.Path) -> None:
    content = f"""
    CustomerId: {fairytale_name}
    BaseRootEmail: panther-hosted@runpanther.io
    CustomerRegion: us-west-2
    DeploymentGroup: a
    CloudFormationParameters:
      CompanyDisplayName: {fairytale_name}
      CustomDomain: {fairytale_name}.runpanther.net
      FirstUserEmail: {fairytale_name}@panther.io
      FirstUserFamilyName: Test
      FirstUserGivenName: User
      OnboardSelf: false
      SentryEnvironment: staging
    """
    _create_deployment_file(content, fairytale_name, parent_dir)


def _read_customer_deployment_file(repo_path: pathlib.Path, fairytale_name: str) -> ruamel.yaml.CommentedMap:
    customer_cfg = str(repo_path / "deployment-metadata" / "deployment-targets" / f"{fairytale_name}.yml")
    return load_yaml_cfg(customer_cfg)


@pytest.fixture
def hosted_deployments_repo(tmp_path: pytest.fixture, no_cfn_params_customer: pytest.fixture,
                            no_sentry_params_customer: pytest.fixture,
                            sentry_params_customer: pytest.fixture) -> pathlib.Path:
    """
    Creates a temporary directory with deployment files. Serves as the hosted deployments repo mock.
    :param sentry_params_customer: custom fixture
    :param no_sentry_params_customer: custom fixture
    :param no_cfn_params_customer: custom fixture
    :param tmp_path: Python's 'tmp_path' fixture
    :return: Absolute path of the hosted deployments repo mock
    """
    git.Repo.init(tmp_path)
    parent_dir = tmp_path / "deployment-metadata" / "deployment-targets"
    parent_dir.mkdir(exist_ok=True, parents=True)
    _create_sentry_customer_file(sentry_params_customer, parent_dir)
    _create_no_sentry_params_customer_file(no_sentry_params_customer, parent_dir)
    _create_no_cfn_params_customer_file(no_cfn_params_customer, parent_dir)
    return tmp_path


class TestDisableCustomerSentryAlerts:
    _TASK = DisableCustomerSentryAlerts(is_dry_run=True)

    @staticmethod
    def _assert_sentry_alerts_disabled(repo_path: pathlib.Path, fairytale_name: str):
        customer_cfg = _read_customer_deployment_file(repo_path, fairytale_name)
        assert customer_cfg["CloudFormationParameters"]["SentryEnvironment"] == "", \
            f"Parameter CloudFormationParameters.SentryEnvironment must be an empty string."

    @staticmethod
    def get_params(repo, fairytale_name):
        return {"hosted_deployments_path": repo, "fairytale_name": fairytale_name, "organization": "hosted"}

    def test_customer_with_sentry_params(self, hosted_deployments_repo, sentry_params_customer):
        params = self.get_params(hosted_deployments_repo, sentry_params_customer)

        self._TASK.run(params)

        self._assert_sentry_alerts_disabled(hosted_deployments_repo, sentry_params_customer)

    def test_customer_with_no_sentry_params(self, hosted_deployments_repo, no_sentry_params_customer):
        params = self.get_params(hosted_deployments_repo, no_sentry_params_customer)

        self._TASK.run(params)

        self._assert_sentry_alerts_disabled(hosted_deployments_repo, no_sentry_params_customer)

    def test_customer_with_no_cfn_params(self, hosted_deployments_repo, no_cfn_params_customer):
        params = self.get_params(hosted_deployments_repo, no_cfn_params_customer)

        self._TASK.run(params)

        self._assert_sentry_alerts_disabled(hosted_deployments_repo, no_cfn_params_customer)


@pytest.mark.manual_test
def test_manual():
    print(
        main({
            "staging_deployments_path": os.getenv("staging-deployments"),
            "fairytale_name": "prev-snowflake",
            "organization": "root"
        }))
