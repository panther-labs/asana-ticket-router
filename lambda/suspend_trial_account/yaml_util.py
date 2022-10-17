from typing import Any
from ruamel.yaml import YAML


def upsert_file_value(filename: str, parameter: str, value: Any) -> None:
    yaml = YAML()
    yaml.preserve_quotes = True
    loaded_yaml = None
    with open(filename, "r") as f:
        loaded_yaml = yaml.load(f.read())

    if not loaded_yaml:
        raise Exception(f"Failed to load any yaml from {filename}")

    param_crumbs = parameter.split(".")
    if len(param_crumbs) < 1:
        raise Exception(
            "Invalid yaml path passed, please pass in using dot notation like 'CloudFormationParams.TrialShutdown'")

    u = loaded_yaml
    for param in param_crumbs[:-1]:
        u[param] = u.get(param, {})
        u = u[param]
    u[param_crumbs[-1]] = value

    with open(filename, "w") as f:
        loaded_yaml = yaml.dump(loaded_yaml, f)

    return


def get_file_value(filename: str, parameter: str) -> Any:
    yaml = YAML()
    yaml.preserve_quotes = True
    loaded_yaml = None
    with open(filename, "r") as f:
        loaded_yaml = yaml.load(f.read())

    if not loaded_yaml:
        raise Exception(f"Failed to load any yaml from {filename}")

    param_crumbs = parameter.split(".")
    if len(param_crumbs) < 1:
        raise Exception(
            "Invalid yaml path passed, please pass in using dot notation like 'CloudFormationParams.TrialShutdown'")

    u = loaded_yaml
    for param in param_crumbs[:-1]:
        u[param] = u.get(param, {})
        u = u[param]
    return u.get(param_crumbs[-1], None)
