import os
from contextlib import contextmanager
import importlib.util


def get_cwd() -> str:
    """
    :return: current working directory
    """
    return os.getcwd()


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


def get_user_directory() -> str:
    """
    :return: user directory, i.e. '~' path
    """
    return os.path.expanduser("~")


def join_paths(path: str, *paths: str) -> str:
    return os.path.join(path, *paths)


def write_to_file(filepath: str, text: str, is_append: bool = True) -> None:
    mode = 'a' if is_append else 'w'
    with open(filepath, mode) as f:
        f.write(text)


@contextmanager
def tmp_change_dir(change_dir: str):
    try:
        cur_dir = get_cwd()
    except FileNotFoundError:
        cur_dir = None

    os.chdir(change_dir)
    try:
        yield
    finally:
        if cur_dir is not None:
            os.chdir(cur_dir)


def load_py_file_as_module(filepath: str):
    """
    :param filepath: Absolute filepath
    :return: Python module object
    """
    spec = importlib.util.spec_from_file_location("module.name", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
