import os
from contextlib import contextmanager


def get_cur_dir_abs_path() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def join_paths(path: str, *paths: str) -> str:
    return os.path.join(path, *paths)


@contextmanager
def tmp_change_dir(change_dir: str):
    cur_dir = get_cur_dir_abs_path()
    os.chdir(change_dir)
    try:
        yield
    finally:
        os.chdir(cur_dir)
