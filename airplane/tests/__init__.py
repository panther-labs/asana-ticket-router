from contextlib import contextmanager

from v2.consts.airplane_env import AirplaneEnv


@contextmanager
def change_airplane_env_var(var_name: str, val: str):
    """Change an Airplane environment variable during a test, and change it back when done.

    :param var_name: Name of the Airplane environment variable
    :param val: Value to set to the env. var
    """
    try:
        old_val = getattr(AirplaneEnv, var_name)
        setattr(AirplaneEnv, var_name, val)
        yield
    finally:
        setattr(AirplaneEnv, var_name, old_val)
