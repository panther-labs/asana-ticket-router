import os

from contextlib import contextmanager


@contextmanager
def tmp_change_dir(change_dir):
    old_dir = os.getcwd()
    os.chdir(change_dir)
    try:
        yield
    finally:
        os.chdir(old_dir)
