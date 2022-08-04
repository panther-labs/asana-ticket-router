import os


class AirplaneEnv:
    AIRPLANE_BASE_URL = "https://app.airplane.dev"
    AIRPLANE_ENV_SLUG = os.getenv("AIRPLANE_ENV_SLUG")
    AIRPLANE_SCHEDULE_ID = os.getenv("AIRPLANE_SCHEDULE_ID")
    AIRPLANE_TASK_ID = os.getenv("AIRPLANE_TASK_ID")
    AIRPLANE_REQUESTER_EMAIL = os.getenv("AIRPLANE_REQUESTER_EMAIL")
    AIRPLANE_RUNNER_ID = os.getenv("AIRPLANE_RUNNER_ID")
    AIRPLANE_RUNNER_EMAIL = os.getenv("AIRPLANE_RUNNER_EMAIL")
    AIRPLANE_RUN_ID = os.getenv("AIRPLANE_RUN_ID")
    AIRPLANE_SESSION_ID = os.getenv("AIRPLANE_SESSION_ID")
    AIRPLANE_TEAM_ID = os.getenv("AIRPLANE_TEAM_ID")

    @classmethod
    def is_local_env(cls):
        return cls.AIRPLANE_RUNNER_ID is None

    @classmethod
    def is_prod_env(cls):
        return cls.AIRPLANE_ENV_SLUG == "prod"

    @classmethod
    def get_task_run_url(cls):
        return os.path.join(cls.AIRPLANE_BASE_URL, "runs", cls.AIRPLANE_RUN_ID)

    @classmethod
    def is_api_user_execution(cls):
        return "service-user" in cls.AIRPLANE_RUNNER_EMAIL
