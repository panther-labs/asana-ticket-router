import importlib.util
import os


def load_py_file_as_module(py_file_path):
    py_path = os.path.abspath(py_file_path)
    spec = importlib.util.spec_from_file_location("module.name", py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
