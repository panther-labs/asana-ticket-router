"""
os_util contains OS-level functions around pathing,
directories, permissions, and files
"""

import importlib.util
import os
import sys


def join_paths(path: str, *paths: str) -> str:
    """
    join_paths takes a base path and joins subsequent paths to it
    """
    return os.path.join(path, *paths)


def change_dir(path: str) -> None:
    """
    change_dir accepts a path and changes to that directory
    """
    print(f"Changing directory to: {path}")
    os.chdir(path)


def get_current_dir() -> str:
    """
    get_current_dir returns the current working directory
    """
    return os.getcwd()


def change_mode(path: str, mode: int) -> None:
    """
    change_mode modifies the permissions (mode) on for a given path
    (e.g., 0400, 0644, 0755, etc.)
    """
    os.chmod(path, mode)


def run_cmd(cmd: str) -> None:
    """
    run_cmd executes a given command
    """
    os.system(cmd)


def append_to_system_path(path: str) -> None:
    """
    append_to_system_path adds the given path to $PATH if it
    is not already present
    """
    if path not in sys.path:
        sys.path.append(path)


def load_py_file_as_module(path: str):
    """
    load_py_file_as_module imports a Python file programmatically
    """
    spec = importlib.util.spec_from_file_location("module.name", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
