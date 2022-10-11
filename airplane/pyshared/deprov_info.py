from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(kw_only=True)
class DeprovInfo:
    aws_account_id: Optional[str] = None
    deprovision_state: Optional[str] = "waiting_for_dns_time"
    dns_removal_time: Optional[str] = None
    organization: Optional[str] = None
    region: Optional[str] = None
    teardown_attempt: Optional[str] = "0"
    teardown_build_id: Optional[str] = "none"
    teardown_time: Optional[str] = None
