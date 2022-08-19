from dataclasses import asdict, dataclass
from datetime import datetime

from pyshared.yaml_utils import change_yaml_file, load_yaml_cfg


@dataclass
class DeprovInfo:
    dns_removal_time: datetime
    teardown_time: datetime


class DeprovInfoDeployFile:
    CFG_KEY = "DeprovisionStatus"
    TIME_FORMAT = "%Y-%M-%D %H:%M:%S"

    def __init__(self, filepath: str):
        self.filepath = filepath

    def retrieve_deprov_info(self) -> DeprovInfo:
        with load_yaml_cfg(self.filepath) as cfg:
            return DeprovInfo(**cfg[self.CFG_KEY])

    def write_deprov_info(self, deprov_info: DeprovInfo):
        with change_yaml_file(self.filepath) as cfg:
            cfg[self.CFG_KEY] = asdict(deprov_info)
