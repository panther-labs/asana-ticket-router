import pytest

from tests import change_airplane_env_var
from v2.task_models.airplane_task import AirplaneTask


class MockAirplaneTask(AirplaneTask):

    def run(self, params: dict):
        pass


def test_api_user_required_for_api_task_execution_failure():
    with change_airplane_env_var(var_name="AIRPLANE_RUNNER_EMAIL", val="my.user@panther.io"):
        with pytest.raises(RuntimeError):
            MockAirplaneTask(api_use_only=True)


def test_api_user_required_for_api_task_execution_success():
    with change_airplane_env_var(var_name="AIRPLANE_RUNNER_EMAIL", val="service-user-usr1234"):
        # Passes by not throwing exceptions
        mock_task = MockAirplaneTask(api_use_only=True)
        mock_task.run(params={})
