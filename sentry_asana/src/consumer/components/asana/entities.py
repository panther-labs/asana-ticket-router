# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


# The URL describing the process we follow for Sentry tickets
RUNBOOK_URL = 'https://www.notion.so/pantherlabs/Sentry-issue-handling-ee187249a9dd475aa015f521de3c8396'


class PRIORITY(Enum):
    """Mapping to Asana Severity IDs"""
    HIGH = '1159524604627933'
    MEDIUM = '1159524604627934'
    LOW = '1159524604627935'  # Not used


class TEAM(Enum):
    """Mapping of all engineering teams"""
    CORE_PRODUCT = 'CORE_PRODUCT'
    DATA_PLATFORM = 'DATA_PLATFORM'
    DETECTIONS = 'DETECTIONS'
    INGESTION = 'INGESTION'
    INVESTIGATIONS = 'INVESTIGATIONS'
    OBSERVABILITY_PERF = 'OBSERVABILITY_PERF'
    PRODUCTIVITY = 'PRODUCTIVITY'
    QUALITY = 'QUALITY'
    SECURITY_IT_COMPLIANCE = 'SECURITY_IT_COMPLIANCE'


@dataclass
class EngTeam:
    """Asana IDs for the team and its associated backlog."""
    team_id: str
    backlog_id: str
    sprint_portfolio_id: str
    sprint_portfolio_id_dev: str


@dataclass
class AsanaFields:  # pylint: disable=too-many-instance-attributes
    """Class for storing the relevant asana fields for creating a task"""
    assigned_team: EngTeam
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


# A mapping of all engineering teams to their Asana IDs
ENG_TEAMS: Dict[TEAM, EngTeam] = {
    TEAM.CORE_PRODUCT: EngTeam(
        team_id='1201305154831714',
        backlog_id='1201267919523621',
        sprint_portfolio_id='1201675315244004',
        sprint_portfolio_id_dev='1201700591175670'
    ),
    TEAM.DATA_PLATFORM: EngTeam(
        team_id='1201305154831715',
        backlog_id='1201282881828563',
        sprint_portfolio_id='1201680779826585',
        sprint_portfolio_id_dev='1201700591175709'
    ),
    TEAM.DETECTIONS: EngTeam(
        team_id='1199906290951721',
        backlog_id='1200908948600035',
        sprint_portfolio_id='1201675315243996',
        sprint_portfolio_id_dev='1201700591175694'
    ),
    TEAM.INGESTION: EngTeam(
        team_id='1199906290951709',
        backlog_id='1200908948600021',
        sprint_portfolio_id='1201675315243992',
        sprint_portfolio_id_dev='1201700591175697'
    ),
    TEAM.INVESTIGATIONS: EngTeam(
        team_id='1199906290951706',
        backlog_id='1200908948600028',
        sprint_portfolio_id='1201675315244000',
        sprint_portfolio_id_dev='1201700591175689'
    ),
    TEAM.OBSERVABILITY_PERF: EngTeam(
        team_id='1201305154831712',
        backlog_id='1201267919523642',
        sprint_portfolio_id='1201680804234024',
        sprint_portfolio_id_dev='1201700591175706'
    ),
    TEAM.PRODUCTIVITY: EngTeam(
        team_id='1201305154831711',
        backlog_id='1201267919523628',
        sprint_portfolio_id='1201680804234034',
        sprint_portfolio_id_dev='1201700591175700'
    ),
    TEAM.QUALITY: EngTeam(
        team_id='1201305154831713',
        backlog_id='1201267919523635',
        sprint_portfolio_id='1201680804234029',
        sprint_portfolio_id_dev='1201700591175703'
    ),
    TEAM.SECURITY_IT_COMPLIANCE: EngTeam(
        team_id='1200813282274945',
        backlog_id='1200908948600049',
        sprint_portfolio_id='1201680804234039',
        sprint_portfolio_id_dev='1201700591175712'
    ),
}


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


class SERVICE(Enum):
    """Mapping of services"""
    ALARM_LOGGER = 'panther-alarm-logger'
    ALERTS_API = 'panther-alerts-api'
    ALERT_DELIVERY_API = 'panther-alert-delivery-api'
    ANALYSIS_API = 'panther-analysis-api'
    APITOKEN_AUTHORIZER = 'panther-apitoken-authorizer'
    ATHENA_ADMIN_API = 'panther-athena-admin-api'
    ATHENA_API = 'panther-athena-api'
    AWS_EVENT_PROCESSOR = 'panther-aws-event-processor'
    CFN_CUSTOM_RESOURCES = 'panther-cfn-custom-resources'
    CLOUDSECURITY_DATALAKE_FORWARDER = 'panther-cloudsecurity-datalake-forwarder'
    CLOUD_PULLER = 'panther-cloud-puller'
    CN_ROUTER = 'panther-cn-router'
    COMPLIANCE_API = 'panther-compliance-api'
    DATABASE_WORKFLOW = 'panther-database-workflow'
    DATACATALOG_COMPACTOR = 'panther-datacatalog-compactor'
    DATACATALOG_COMPACTOR_CALLBACKS = 'panther-datacatalog-compactor-callbacks'
    DATACATALOG_COMPACTOR_REAPER = 'panther-datacatalog-compactor-reaper'
    DATACATALOG_UPDATER = 'panther-datacatalog-updater'
    DATA_ARCHIVER = 'panther-data-archiver'
    DETECTIONS_ENGINE = 'panther-detections-engine'
    GRAPH_API = 'panther-graph-api'
    GREYNOISE_PROCESSOR = 'panther-greynoise-processor'
    HOLDING_TANK = 'panther-holding-tank'
    LAYER_MANAGER = 'panther-layer-manager'
    LOGTYPES_API = 'panther-logtypes-api'
    LOG_ALERT_FORWARDER = 'panther-log-alert-forwarder'
    LOG_PROCESSOR = 'panther-log-processor'
    LOG_PULLER = 'panther-log-puller'
    LOG_ROUTER = 'panther-log-router'
    LOOKUP_TABLES_API = 'panther-lookup-tables-api'
    MESSAGE_FORWARDER = 'panther-message-forwarder'
    METRICS_API = 'panther-metrics-api'
    OPS_TOOLS = 'panther-ops-tools'
    ORGANIZATION_API = 'panther-organization-api'
    OUTPUTS_API = 'panther-outputs-api'
    PIP_LAYER_BUILDER = 'panther-pip-layer-builder'
    POLICY_ENGINE = 'panther-policy-engine'
    REPLAY_API = 'panther-replay-api'
    REPLAY_LOG_PUSHER = 'panther-replay-log-pusher'
    RESOURCES_API = 'panther-resources-api'
    RESOURCE_PROCESSOR = 'panther-resource-processor'
    RULES_ENGINE = 'panther-rules-engine'
    SNAPSHOT_POLLERS = 'panther-snapshot-pollers'
    SNAPSHOT_SCHEDULER = 'panther-snapshot-scheduler'
    SNOWFLAKE_ADMIN_API = 'panther-snowflake-admin-api'
    SNOWFLAKE_API = 'panther-snowflake-api'
    SOURCE_API = 'panther-source-api'
    SYSTEM_STATUS = 'panther-system-status'
    TOKEN_AUTHORIZER = 'panther-token-authorizer'  # nosec
    USERS_API = 'panther-users-api'


# Mapping of teams to services. We define this dict
# for readability, but genenerate a SERVICE_TO_TEAM
# mapping for application use.
_TEAM_TO_SERVICE: Dict[TEAM, List[SERVICE]] = {
    TEAM.DETECTIONS: [
        SERVICE.ANALYSIS_API,
        SERVICE.AWS_EVENT_PROCESSOR,
        SERVICE.CLOUDSECURITY_DATALAKE_FORWARDER,
        SERVICE.COMPLIANCE_API,
        SERVICE.DETECTIONS_ENGINE,
        SERVICE.LAYER_MANAGER,
        SERVICE.PIP_LAYER_BUILDER,
        SERVICE.POLICY_ENGINE,
        SERVICE.REPLAY_API,
        SERVICE.REPLAY_LOG_PUSHER,
        SERVICE.RESOURCES_API,
        SERVICE.RESOURCE_PROCESSOR,
        SERVICE.SNAPSHOT_POLLERS,
        SERVICE.SNAPSHOT_SCHEDULER,
    ],
    TEAM.INGESTION: [
        SERVICE.CLOUD_PULLER,
        SERVICE.DATA_ARCHIVER,
        SERVICE.HOLDING_TANK,
        SERVICE.LOGTYPES_API,
        SERVICE.LOG_PROCESSOR,
        SERVICE.LOG_PULLER,
        SERVICE.LOG_ROUTER,
        SERVICE.MESSAGE_FORWARDER,
        SERVICE.RULES_ENGINE,
        SERVICE.SOURCE_API,
        SERVICE.SYSTEM_STATUS,
    ],
    TEAM.INVESTIGATIONS: [
        SERVICE.ALERTS_API,
        SERVICE.ALERT_DELIVERY_API,
        SERVICE.ATHENA_ADMIN_API,
        SERVICE.ATHENA_API,
        SERVICE.DATABASE_WORKFLOW,
        SERVICE.DATACATALOG_COMPACTOR,
        SERVICE.DATACATALOG_COMPACTOR_CALLBACKS,
        SERVICE.DATACATALOG_COMPACTOR_REAPER,
        SERVICE.DATACATALOG_UPDATER,
        SERVICE.GREYNOISE_PROCESSOR,
        SERVICE.LOG_ALERT_FORWARDER,
        SERVICE.LOOKUP_TABLES_API,
        SERVICE.OUTPUTS_API,
        SERVICE.SNOWFLAKE_ADMIN_API,
        SERVICE.SNOWFLAKE_API
    ],
    TEAM.CORE_PRODUCT: [
        SERVICE.APITOKEN_AUTHORIZER,
        SERVICE.CFN_CUSTOM_RESOURCES,
        SERVICE.CN_ROUTER,
        SERVICE.GRAPH_API,
        SERVICE.METRICS_API,
        SERVICE.ORGANIZATION_API,
        SERVICE.TOKEN_AUTHORIZER,
        SERVICE.USERS_API
    ],
    TEAM.OBSERVABILITY_PERF: [
        SERVICE.ALARM_LOGGER
    ],
    TEAM.PRODUCTIVITY: [
        SERVICE.OPS_TOOLS
    ]
}

# Obtain mapping of individual services values to teams
SERVICE_TO_TEAM: Dict[str, TEAM] = {
    service.value: team for team, services in _TEAM_TO_SERVICE.items()
    for service in services
}


class FE_SERVICE(Enum):  # pylint: disable=invalid-name
    """Mapping of FE Services"""
    ALERTS_AND_ERRORS = '/alerts-and-errors/'
    ANALYSIS = '/analysis/'
    CLOUD_ACCOUNTS = '/cloud-accounts/'
    DATA_MODELS = '/data-models/'
    DATA_SCHEMAS = '/data-schemas/'
    DESTINATIONS = '/destinations/'
    DETECTIONS = '/detections/'
    ENRICHMENT = '/enrichment/'
    EXPLORER = '/explorer/'
    HELPERS = '/helpers/'
    INDICATOR_SEARCH = '/indicator-search/'
    LOG_SOURCES = '/log-sources/'
    OVERVIEW = '/overview/'
    QUERY_HISTORY = '/query-history/'
    RESOURCES = '/resources/'
    SAVED_QUERIES = '/saved-queries/'


_TEAM_TO_FE_SERVICE: Dict[TEAM, List[FE_SERVICE]] = {
    TEAM.DETECTIONS: [
        FE_SERVICE.ANALYSIS,
        FE_SERVICE.DATA_MODELS,
        FE_SERVICE.DESTINATIONS,
        FE_SERVICE.DETECTIONS,
        FE_SERVICE.HELPERS,
        FE_SERVICE.OVERVIEW,
        FE_SERVICE.RESOURCES,
    ],
    TEAM.INVESTIGATIONS: [
        FE_SERVICE.ALERTS_AND_ERRORS,
        FE_SERVICE.ENRICHMENT,
        FE_SERVICE.EXPLORER,
        FE_SERVICE.INDICATOR_SEARCH,
        FE_SERVICE.QUERY_HISTORY,
        FE_SERVICE.SAVED_QUERIES,
    ],
    TEAM.INGESTION: [
        FE_SERVICE.CLOUD_ACCOUNTS,
        FE_SERVICE.DATA_SCHEMAS,
        FE_SERVICE.LOG_SOURCES,
    ]
}

# Obtain mapping of individual FE services values to teams
FE_SERVICE_TO_TEAM: Dict[str, TEAM] = {
    service.value: team for team, services in _TEAM_TO_FE_SERVICE.items()
    for service in services
}


class CUSTOMFIELD(Enum):
    """Mapping of Custom Asana Field IDs"""
    ESTIMATE = '1199944595440874'
    # Deprecated
    # IMPACTED = '1200216708142306'
    # ONE_CUSTOMER = '1200822942218893'
    INVESTIGATE = '1200218109698442'
    PRIORITY = '1159524604627932'
    REPORTER = '1200165681182165'
    SENTRY_IO = '1200198568911550'
    # TODO: remove TASK_TYPE after TYPE and ON_CALL are defined.
    TASK_TYPE = '1199912337121892'
    TEAM = '1199906290951705'
