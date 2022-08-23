from v2.consts.airplane_env import AirplaneEnv


def main(params: dict):
    if AirplaneEnv.is_api_user_execution():
        print(f"Ha, you got zapped nerd: {params}")
    else:
        print(f"You still got zapped non-api nerd! {params}")
