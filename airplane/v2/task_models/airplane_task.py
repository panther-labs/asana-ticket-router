import traceback

from slack_sdk import WebClient

from v2.consts.airplane_env import AirplaneEnv
from v2.pyshared.aws_secrets import get_secret_value


class AirplaneTask:

    def __init__(self, is_dry_run: bool = False):
        """
        :param is_dry_run: Flag indicating a dry run
        """
        self.is_dry_run = is_dry_run

    def run(self, params: dict) -> any:
        """
        Main method of an Airplane task. Must be implemented in the concrete class
        :param params: Airplane parameters
        :return: Any value or None
        """
        raise NotImplementedError("The method must be implemented in the concrete class.")

    def run_notify_failures(self, params: dict) -> any:
        """Same as run function, but it sends a Slack message to the failure channel if it fails."""
        try:
            return self.run(params)
        except Exception:
            if AirplaneEnv.is_prod_env():
                self.send_slack_message(
                    channel_name=self.get_failure_slack_channel(),
                    message=f"Airplane task {AirplaneEnv.get_task_run_url()} failed:\n```{traceback.format_exc()}```"
                )
            raise

    @staticmethod
    def get_failure_slack_channel():
        """Failure notifications will be directed to this channel if main_notify_failures is called."""
        return ""

    @staticmethod
    def send_slack_message(channel_name: str, message: str):
        """
        Sends a message via the Airplane Notifications app. That app must be a member of the given channel.

        :param channel_name: #slack-channel-name
        :param message: Message to send to channel
        """
        slack_client = WebClient(token=get_secret_value(secret_name="airplane/slack-airplane-notifications-token"))
        slack_client.chat_postMessage(channel=channel_name, text=message)
