import os
from contextlib import contextmanager


def get_cwd() -> str:
    """
    :return: current working directory
    """
    return os.getcwd()


def get_current_directory(__file__: str) -> str:
    """
    :param __file__: '__file__' attribute of the caller's script
    :return: absolute path of the caller's script directory
    """
    return os.path.dirname(os.path.abspath(__file__))


def join_paths(path: str, *paths: str) -> str:
    return os.path.join(path, *paths)


@contextmanager
def tmp_change_dir(change_dir: str):
    cur_dir = get_cwd()
    os.chdir(change_dir)
    try:
        yield
    finally:
        os.chdir(cur_dir)
