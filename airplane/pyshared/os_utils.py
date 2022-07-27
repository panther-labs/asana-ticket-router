import os

from contextlib import contextmanager


@contextmanager
def tmp_change_dir(change_dir):
    try:
        old_dir = os.getcwd()
    except FileNotFoundError:
        old_dir = None

    os.chdir(change_dir)
    try:
        yield
    finally:
        if old_dir is not None:
            os.chdir(old_dir)


def list_files(path):
    files = []
    for name in os.listdir(path):
        if os.path.isfile(os.path.join(path, name)):
            files.append(name)
    return files
