import glob

from pyshared.airplane_utils import AirplaneTask
from pyshared.git_ops import git_clone
from pyshared.load_py_file import load_py_file_as_module


class FairytaleNameGenerator(AirplaneTask):

    def main(self, params):
        # Why pass in the fairytale name and just return it?
        # So Airplane runbooks can use this task to standardize an output variable future blocks can use, whether a new
        # name is generated or an existing one is used.
        fairytale_name = params.get("fairytale_name")
        if not fairytale_name:
            repo_dir = git_clone(repo="hosted-deployments", github_setup=True)
            py_file = glob.glob(f"{repo_dir}/**/fairytale_name.py", recursive=True)[0]
            fairytale_name_module = load_py_file_as_module(py_file_path=py_file)
            fairytale_name = fairytale_name_module.generate_name()
        return {"fairytale_name": fairytale_name}


def main(params):
    return FairytaleNameGenerator().main(params)
