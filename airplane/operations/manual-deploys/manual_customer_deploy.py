import datetime

from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.load_py_file import load_py_file_as_module
from pyshared.os_utils import tmp_change_dir
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg


def _update_cfg_file(name):
    cfg_filepath = f"deployment-metadata/deployment-targets/{name}.yml"

    cfg = load_yaml_cfg(cfg_filepath=cfg_filepath, error_msg=f"Customer deployment file not found: '{cfg_filepath}'")
    cfg["ManualDeploy"] = str(datetime.datetime.now())
    save_yaml_cfg(cfg_filepath=cfg_filepath, cfg=cfg)


def _gen_cfgs():
    generate_filepath = "automation-scripts/generate.py"
    generate_mod = load_py_file_as_module(py_file_path=generate_filepath)
    generate_mod.generate_configs()


def main(params):
    name = params["fairytale_name"]
    test_run = params["airplane_test_run"]
    hosted_deploy_dir = git_clone(repo="hosted-deployments",
                                  github_setup=True,
                                  existing_dir=params.get("hosted_deploy_dir"))

    with tmp_change_dir(change_dir=hosted_deploy_dir):
        _update_cfg_file(name=name)
        _gen_cfgs()
        git_add_commit_push(files=("deployment-metadata", ), title=f"Manually redeploy {name}", test_run=test_run)
