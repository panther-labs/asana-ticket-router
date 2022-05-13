import os

from pyshared import onepass
from v2.consts.airplane_env import AirplaneEnv


class AirplaneTask:
    AIRPLANE_BASE_URL = "https://app.airplane.dev"
    test_roles = {}

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

    def main(self):
        raise NotImplementedError

    @staticmethod
    def add_test_role(role_key, role_value, region=None):
        """Only for testing - don't use as part of an Airplane run, it will fail!"""
        AirplaneTask.test_roles[role_key] = (role_value, region)

    @staticmethod
    def set_env_var_from_onepass_item(env_var_name, onepass_item_name):
        """Only for testing - don't use as part of an Airplane run, it will fail!"""
        if env_var_name not in os.environ:
            os.environ[env_var_name] = onepass.get_item(onepass_item_name)


def set_local_run():
    os.environ["local_run"] = "true"


def is_local_run():
    return os.environ.get("local_run", "") == "true"


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
