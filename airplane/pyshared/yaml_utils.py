import dateutil.parser
from contextlib import contextmanager
from ruamel.yaml import YAML, comments


def timestamp_constructor(loader, node):
    return dateutil.parser.parse(node.value)


def _yaml_instance() -> YAML:
    yaml = YAML(pure=True)
    yaml.constructor.add_constructor(u'tag:yaml.org,2002:timestamp', timestamp_constructor)
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def load_yaml_cfg(cfg_filepath: str, error_msg: str = None) -> comments.CommentedMap:
    error_msg = error_msg if (error_msg is not None) else f"Could not find `{cfg_filepath}'"

    try:
        with open(cfg_filepath, "r") as cfg_file:
            return _yaml_instance().load(cfg_file)
    except FileNotFoundError:
        raise ValueError(error_msg)


def save_yaml_cfg(cfg_filepath: str, cfg: comments.CommentedMap):
    with open(cfg_filepath, 'w') as cfg_file:
        _yaml_instance().dump(cfg, cfg_file)


@contextmanager
def change_yaml_file(cfg_filepath: str, error_msg: str = None):
    cfg = load_yaml_cfg(cfg_filepath=cfg_filepath, error_msg=error_msg)
    yield cfg
    save_yaml_cfg(cfg_filepath=cfg_filepath, cfg=cfg)
