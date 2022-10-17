import importlib.util
import os
import sys


def join_paths(path: str, *paths: str) -> str:
    return os.path.join(path, *paths)


def change_dir(path: str) -> None:
    print(f"Changing directory to: {path}")
    os.chdir(path)


def get_current_dir() -> str:
    return os.getcwd()


def change_mode(path: str, mode: int) -> None:
    os.chmod(path, mode)


def run_cmd(cmd: str) -> None:
    os.system(cmd)


def append_to_system_path(path: str) -> None:
    if path not in sys.path:
        sys.path.append(path)


def load_py_file_as_module(path: str):
    spec = importlib.util.spec_from_file_location("module.name", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
