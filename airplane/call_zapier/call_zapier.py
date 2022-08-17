import os

from v2.consts.airplane_env import AirplaneEnv


def main(params: dict):
    username = params.get("username", "DefaultedInTask")
    if AirplaneEnv.is_api_user_execution():
        print(f"Ha, you got zapped nerd: {username}")
    else:
        print(f"You still got zapped non-api nerd! {username}")

