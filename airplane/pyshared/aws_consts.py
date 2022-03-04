import os

_PYSHARED_DIR = os.path.dirname(os.path.realpath(__file__))
_ARN_FILE = os.path.join(_PYSHARED_DIR, "..", "util", "aws-consts")
_aws_consts = {}
with open(_ARN_FILE) as arn_file:
    for line in arn_file.readlines():
        key, val = line.split("=")
        _aws_consts[key] = val.strip("\n").strip('"')


def get_aws_const(const_name: str) -> str:
    """See utils/aws-consts for list of choices"""
    try:
        return _aws_consts[const_name]
    except KeyError:
        raise ValueError(f"Invalid const_name: {const_name}. Valid arn_names: {list(_aws_consts.keys())}")
