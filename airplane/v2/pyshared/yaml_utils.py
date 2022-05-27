from contextlib import contextmanager
from ruamel.yaml import YAML, comments


def _yaml_instance() -> YAML:
    yaml = YAML(pure=True)
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def is_comment_in_yaml_file(comment: str, cfg_yaml: comments.CommentedMap) -> bool:
    """
    Checks whether a given substring is part of the yaml file comments.
    :param comment: Substring to find in the yaml file comments
    :param cfg_yaml: Ruamel instance of a yaml file
    :return: bool
    """
    return comment in cfg_yaml.ca


def add_top_level_comment(comment: str, cfg_yaml: comments.CommentedMap) -> None:
    cfg_yaml.yaml_set_start_comment(comment)


def remove_top_level_comments(cfg_yaml: comments.CommentedMap) -> None:
    """
    Removes all comments preceeding the first yaml key-value pair.
    :param cfg_yaml: Ruamel instance of a yaml file
    :return: None
    """
    cfg_yaml.ca.comment = None


def get_top_level_comments(cfg_yaml: comments.CommentedMap) -> list[str]:
    """
    Returns all comments preceeding the first yaml key-value pair. Each new-line comment will be a separate element.
    :param cfg_yaml: Ruamel instance of a yaml file
    :return: list of comments without the '#' sign
    """
    comment_list = []
    if cfg_yaml.ca.comment:
        raw_comment_list = cfg_yaml.ca.comment[1]
        comment_list = [rc.value.removeprefix("#").strip() for rc in raw_comment_list]
    return comment_list


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
