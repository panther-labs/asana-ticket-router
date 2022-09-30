import os
import tempfile
import traceback

from slack_sdk import WebClient

from v2.consts.airplane_env import AirplaneEnv
from v2.pyshared.aws_secrets import get_secret_value


class AirplaneTask:

    def __init__(self, is_dry_run: bool = False, api_use_only=False, requires_runbook=False):
        """
        :param is_dry_run: Flag indicating a dry run
        """
        self.validate_api_user(api_use_only)
        self.validate_task_run_from_a_runbook(requires_runbook)
        self.is_dry_run = is_dry_run
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.task_dir = self.tmp_dir.name
        os.chdir(self.task_dir)

    def run(self, params: dict) -> any:
        """
        Main method of an Airplane task. Must be implemented in the concrete class
        :param params: Airplane parameters
        :return: Any value or None
        """
        raise NotImplementedError("The method must be implemented in the concrete class.")

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
    def validate_api_user(api_use_only: bool):
        if api_use_only and not AirplaneEnv.is_api_user_execution():
            raise RuntimeError("This task is only executable by the airplane API!")

    @staticmethod
    def validate_task_run_from_a_runbook(requires_runbook: bool):
        if requires_runbook and not AirplaneEnv.AIRPLANE_SESSION_ID:
            raise RuntimeError("This task must be run from within a runbook!")
