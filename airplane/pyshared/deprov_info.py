from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

from pyshared.yaml_utils import change_yaml_file, load_yaml_cfg


@dataclass
class DeprovInfo:
    dns_removal_time: Optional[datetime] = None
    teardown_time: Optional[datetime] = None
    aws_account_id: Optional[str] = None
    organization: Optional[str] = None


class DeprovInfoDeployFile:
    CFG_KEY = "DeprovisionStatus"

    def __init__(self, filepath: str):
        self.filepath = filepath

    def retrieve_deprov_info(self) -> DeprovInfo:
        cfg = load_yaml_cfg(self.filepath, load_tz=True)
        return DeprovInfo(**cfg.get(self.CFG_KEY, {}))

    def remove_deprov_info(self):
        with change_yaml_file(self.filepath) as cfg:
            cfg.pop(self.CFG_KEY, None)

    def write_deprov_info(self, deprov_info: DeprovInfo):
        with change_yaml_file(self.filepath) as cfg:
            cfg[self.CFG_KEY] = asdict(deprov_info)

    def dns_removed(self):
        info = self.retrieve_deprov_info()
        return (info.teardown_time is not None) and (info.dns_removal_time is None)
