import os


class AirplaneEnv:
    AIRPLANE_SCHEDULE_ID = os.getenv("AIRPLANE_SCHEDULE_ID")
    AIRPLANE_TASK_ID = os.getenv("AIRPLANE_TASK_ID")
    AIRPLANE_RUNNER_ID = os.getenv("AIRPLANE_RUNNER_ID")
    AIRPLANE_RUNNER_EMAIL = os.getenv("AIRPLANE_RUNNER_EMAIL")
    AIRPLANE_RUN_ID = os.getenv("AIRPLANE_RUN_ID")

    @classmethod
    def is_local_env(cls):
        return cls.AIRPLANE_RUNNER_ID is None
