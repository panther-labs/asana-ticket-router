from ruamel.yaml import YAML


def load_yaml_cfg(cfg_filepath, error_msg=None):
    error_msg = error_msg if (error_msg is not None) else f"Could not find `{cfg_filepath}'"

    try:
        with open(cfg_filepath, "r") as cfg_file:
            return YAML(pure=True).load(cfg_file)
    except FileNotFoundError:
        raise ValueError(error_msg)


def save_yaml_cfg(cfg_filepath, cfg):
    with open(cfg_filepath, 'w') as cfg_file:
        YAML(pure=True).dump(cfg, cfg_file)
