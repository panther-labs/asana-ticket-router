# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from enum import Enum
from typing import Dict, List
from dataclasses import dataclass

from common.components.entities import service


# The URL describing the process we follow for Sentry tickets
RUNBOOK_URL = 'https://www.notion.so/pantherlabs/Sentry-issue-handling-ee187249a9dd475aa015f521de3c8396'


class PRIORITY(Enum):
    """Mapping to Asana Severity IDs"""
    HIGH = '1159524604627933'
    MEDIUM = '1159524604627934'
    LOW = '1159524604627935'  # Not used


@dataclass
class AsanaFields:  # pylint: disable=too-many-instance-attributes
    """Class for storing the relevant asana fields for creating a task"""
    assigned_team: service.EngTeam
    aws_account_id: str
    aws_region: str
    customer: str
    display_name: str
    environment: str
    event_datetime: str
    priority: PRIORITY
    project_gids: List[str]
    runbook_url: str
    tags: Dict
    title: str
    url: str


# A list of hardcoded Account IDs for our self hosted customers, as extracted via
# https://github.com/panther-labs/aws-management-cloudformation/blob/master/panther-public/enterprise-accounts.yml
SELF_HOSTED_ACCOUNTS_IDS = [
    '880172401261',  # Grail,
    '346666025108',  # Infoblox IT,
    '405093580753',  # Infoblox dev,
    '718190095844',  # Infoblox prod,
    '971535947767',  # Coinbase dev
    '817873525313',  # Coinbase prod
]

class CUSTOMFIELD(Enum):
    """Mapping of Custom Asana Field IDs"""
    ESTIMATE = '1199944595440874'
    ON_CALL = '1202118168254133'
    PRIORITY = '1159524604627932'
    REPORTER = '1200165681182165'
    SENTRY_IO = '1200198568911550'
    EPD_TASK_TYPE = '1202118168254120'
    TEAM = '1199906290951705'
    OUTCOME_FIELD = '1202091103836330'
    OUTCOME_TYPE_KTLO = '1202091103836337'
