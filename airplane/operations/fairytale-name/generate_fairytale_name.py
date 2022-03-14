import glob

from pyshared.git_ops import git_clone
from pyshared.load_py_file import load_py_file_as_module


def main(params):
    repo_dir = git_clone(repo="hosted-deployments", github_setup=True)
    py_file = glob.glob(f"{repo_dir}/**/fairytale_name.py", recursive=True)[0]
    fairytale_name_module = load_py_file_as_module(py_file_path=py_file)
    return {"fairytale_name": fairytale_name_module.generate_name()}
