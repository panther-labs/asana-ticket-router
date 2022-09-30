import os
import tempfile
import traceback

from v2.pyshared.aws_secrets import get_secret_value
from slack_sdk import WebClient

from pyshared import onepass
from v2.consts.airplane_env import AirplaneEnv


class AirplaneTask:
    AIRPLANE_BASE_URL = "https://app.airplane.dev"
    test_roles = {}

    def __init__(self, api_use_only=False, requires_runbook=False):
        self.validate_api_user(api_use_only)
        self.validate_task_run_from_a_runbook(requires_runbook)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.task_dir = self.tmp_dir.name
        os.chdir(self.task_dir)

    @staticmethod
    def is_test_run():
        return is_test_run(ap_params={})

    @staticmethod
    def get_task_run_url():
        return os.path.join(AirplaneTask.AIRPLANE_BASE_URL, "runs", AirplaneEnv.AIRPLANE_RUN_ID)

    @staticmethod
    def get_runbook_run_url():
        return os.path.join(AirplaneTask.AIRPLANE_BASE_URL, "sessions", AirplaneEnv.AIRPLANE_SESSION_ID)

    @staticmethod
    def get_task_url():
        return os.path.join(AirplaneTask.AIRPLANE_BASE_URL, "tasks", AirplaneEnv.AIRPLANE_TASK_ID)

    def main(self, params: dict = {}):
        raise NotImplementedError

    @staticmethod
    def send_slack_message(channel_name: str, message: str):
        """
        Sends a message via the Airplane Notifications app. That app must be a member of the given channel.

        :param channel_name: #slack-channel-name
        :param message: Message to send to channel
        """
        slack_client = WebClient(token=get_secret_value(secret_name="airplane/slack-airplane-notifications-token"))
        slack_client.chat_postMessage(channel=channel_name, text=message)

    @staticmethod
    def add_test_role(role_key, role_value, region=None):
        """Only for testing - don't use as part of an Airplane run, it will fail!"""
        AirplaneTask.test_roles[role_key] = (role_value, region)

    @staticmethod
    def set_env_var_from_onepass_item(env_var_name, onepass_item_name):
        """Only for testing - don't use as part of an Airplane run, it will fail!"""
        if env_var_name not in os.environ:
            os.environ[env_var_name] = onepass.get_item(onepass_item_name)

    @staticmethod
    def validate_api_user(api_use_only: bool):
        if api_use_only and not AirplaneEnv.is_api_user_execution():
            raise RuntimeError("This task is only executable by the airplane API!")

    @staticmethod
    def validate_task_run_from_a_runbook(requires_runbook: bool):
        if requires_runbook and not AirplaneEnv.AIRPLANE_SESSION_ID:
            raise RuntimeError("This task must be run from within a runbook!")


def set_local_run():
    os.environ["local_run"] = "true"


def is_local_run():
    return AirplaneEnv.is_local_env()


def is_prod_env():
    return os.getenv("AIRPLANE_ENV_SLUG") == "prod"


def is_test_run(ap_params):
    test_run = ap_params.get("airplane_test_run")

    if test_run is None:
        env_slug = os.environ.get("AIRPLANE_ENV_SLUG")
        if env_slug is not None:
            is_staging_or_prod = ("staging" in env_slug) or ("prod" in env_slug)
            test_run = not is_staging_or_prod
        else:
            test_run = True

    if test_run:
        print("*** THIS IS A TEST RUN ***")
    return test_run
