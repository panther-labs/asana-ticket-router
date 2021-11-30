# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import os
from typing import Any, Dict, List
from unittest import TestCase
from unittest.mock import MagicMock, patch

from asana import error as AsanaError

from ..src.enum.priority import AsanaPriority
from ..src.enum import teams
from ..src.service.asana_service import AsanaService


class TestAsanaService(TestCase):
    """Unit Testing Class for AsanaService"""
    _env_vars = {
        'DEV_ASANA_SENTRY_PROJECT': 'dev-project'
    }

    def test_get_owning_team_with_exact_match_server_name(self) -> None:
        # Arrange
        expected_result = teams.INGESTION

        # Act
        result = AsanaService._get_owning_team('panther-log-router')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_fnmatch_server_name(self) -> None:
        # Arrange
        expected_result = teams.DETECTIONS

        # Act
        result = AsanaService._get_owning_team('panther-remediation-api')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_fnmatch_server_name_2(self) -> None:
        # Arrange
        expected_result = teams.INGESTION

        # Act
        result = AsanaService._get_owning_team('panther-log-alpha')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_no_match_server_name(self) -> None:
        # Arrange
        expected_result = teams.CORE_PRODUCT

        # Act
        result = AsanaService._get_owning_team('alpha-beta')

        # Assert
        self.assertEqual(result, expected_result)
    def test_get_previous_asana_link_none(
        self,
    ) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        # The following JSON payload is from the Asana client library
        # instead of the REST API. The only difference is that the client
        # request removes the top level 'data' key containing the payload.
        #
        # Also removed the following for visibility:
        # - `custom_fields` list that was massive
        mock_asana_client.tasks.find_by_id.return_value = {
            "gid": "1201413464115989",
            "assignee": {
                "gid": "1200567447162380",
                "name": "Yusuf Akhtar",
                "resource_type": "user"
            },
            "assignee_status": "inbox",
            "completed": False,
            "completed_at": None,
            "created_at": "2021-11-23T01:08:03.035Z",
            "due_at": None,
            "due_on": None,
            "followers": [
                {
                    "gid": "1199946235851409",
                    "name": "Nick Angelou",
                    "resource_type": "user"
                },
                {
                    "gid": "1200567447162380",
                    "name": "Yusuf Akhtar",
                    "resource_type": "user"
                }
            ],
            "hearted": False,
            "hearts": [],
            "liked": False,
            "likes": [],
            "memberships": [
                {
                    "project": {
                        "gid": "1200611106362920",
                        "name": "Sandbox Asana Project (primarily for testing Sentry Asana automation)",
                        "resource_type": "project"
                    },
                    "section": {
                        "gid": "1200611106362921",
                        "name": "Requirements & Planning",
                        "resource_type": "section"
                    }
                }
            ],
            "modified_at": "2021-11-23T01:08:39.091Z",
            # pylint: disable=line-too-long
            "name": "log-puller: returned an error: *genericapi.LambdaError: failed to get source info for integration ID 2f282bf4-dd69-4823-8894-171c21dcf8bb: failed to fetc...",
            "notes": "Sentry Issue URL: https://sentry.io/organizations/panther-labs/issues/2471853882\n\nEvent Datetime: 2021-11-23T01:07:47.643644Z\n\nCustomer Impacted: Unknown\n\nEnvironment: dev\n\n",
            # pylint: enable=line-too-long
            "num_hearts": 0,
            "num_likes": 0,
            "parent": None,
            "permalink_url": "https://app.asana.com/0/1200611106362920/1201413464115989",
            "projects": [
                {
                    "gid": "1200611106362920",
                    "name": "Sandbox Asana Project (primarily for testing Sentry Asana automation)",
                    "resource_type": "project"
                }
            ],
            "resource_type": "task",
            "start_at": None,
            "start_on": None,
            "tags": [],
            "resource_subtype": "default_task",
            "workspace": {
                "gid": "1159526352574257",
                "name": "Panther Labs",
                "resource_type": "workspace"
            }
        }
        asana_service = AsanaService(mock_asana_client, False)

        # Act
        root_asana_link = asana_service.extract_root_asana_link('1201413464115989')

        # Assert
        mock_asana_client.tasks.find_by_id.assert_called_with('1201413464115989')
        assert root_asana_link is None

    def test_get_previous_asana_link_success(
        self,
    ) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        # The following JSON payload is from the Asana client library
        # instead of the REST API. The only difference is that the client
        # request removes the top level 'data' key containing the payload.
        #
        # Also removed the following for visibility:
        # - `custom_fields` list that was massive
        mock_asana_client.tasks.find_by_id.return_value = {
            "gid": "1201413464115989",
            "assignee": {
                "gid": "1200567447162380",
                "name": "Yusuf Akhtar",
                "resource_type": "user"
            },
            "assignee_status": "inbox",
            "completed": False,
            "completed_at": None,
            "created_at": "2021-11-23T01:08:03.035Z",
            "due_at": None,
            "due_on": None,
            "followers": [
                {
                    "gid": "1199946235851409",
                    "name": "Nick Angelou",
                    "resource_type": "user"
                },
                {
                    "gid": "1200567447162380",
                    "name": "Yusuf Akhtar",
                    "resource_type": "user"
                }
            ],
            "hearted": False,
            "hearts": [],
            "liked": False,
            "likes": [],
            "memberships": [
                {
                    "project": {
                        "gid": "1200611106362920",
                        "name": "Sandbox Asana Project (primarily for testing Sentry Asana automation)",
                        "resource_type": "project"
                    },
                    "section": {
                        "gid": "1200611106362921",
                        "name": "Requirements & Planning",
                        "resource_type": "section"
                    }
                }
            ],
            "modified_at": "2021-11-23T01:08:39.091Z",
            # pylint: disable=line-too-long
            "name": "log-puller: returned an error: *genericapi.LambdaError: failed to get source info for integration ID 2f282bf4-dd69-4823-8894-171c21dcf8bb: failed to fetc...",
            "notes": "Previous Asana Task: https://app.asana.com/0/0/000\n\nRoot Asana Task: https://app.asana.com/0/0/999\n\nSentry Issue URL: https://sentry.io/organizations/panther-labs/issues/2471853882\n\nEvent Datetime: 2021-11-23T01:07:47.643644Z\n\nCustomer Impacted: Unknown\n\nEnvironment: dev\n\n",
            # pylint: enable=line-too-long
            "num_hearts": 0,
            "num_likes": 0,
            "parent": None,
            "permalink_url": "https://app.asana.com/0/1200611106362920/1201413464115989",
            "projects": [
                {
                    "gid": "1200611106362920",
                    "name": "Sandbox Asana Project (primarily for testing Sentry Asana automation)",
                    "resource_type": "project"
                }
            ],
            "resource_type": "task",
            "start_at": None,
            "start_on": None,
            "tags": [],
            "resource_subtype": "default_task",
            "workspace": {
                "gid": "1159526352574257",
                "name": "Panther Labs",
                "resource_type": "workspace"
            }
        }
        asana_service = AsanaService(mock_asana_client, False)

        # Act
        root_asana_link = asana_service.extract_root_asana_link('1201413464115989')

        # Assert
        mock_asana_client.tasks.find_by_id.assert_called_with('1201413464115989')
        assert root_asana_link == 'https://app.asana.com/0/0/999'

    @patch.object(AsanaService, '_get_owning_team')
    def test_create_asana_task_from_sentry_event_with_prev_asana_link_no_root(
            self,
            mock_get_owning_team: Any
        ) -> None:
        # Arrange
        mock_get_owning_team.return_value = teams.CORE_PRODUCT
        sentry_event = {
            "datetime":"2021-07-14T00:10:08.299179Z",
            "environment":"prod",
            "level": "error",
            "tags":[
                [
                    "customer_name",
                    "alpha"
                ],
                [
                    "server_name",
                    "panther-snapshot-pollers"
                ]
            ],
            "timestamp":1626221408.299179,
            "title":"some-title",
            "url":"https://url.com/a/",
            "web_url":"https://url.com/b/",
            "issue_url":"https://url.com/c/",
        }
        mock_asana_client = MagicMock()
        mock_asana_client.tasks.create_task.return_value = {
            "gid": "12345",
            "resource_type": "project",
            "name": "new project"
        }
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = 'current_eng_sprint_id'
        asana_service._current_release_testing_project_id = 'current_release_testing_project_id'
        expected_result = {
            'name': "some-title",
            'projects': ['current_eng_sprint_id'],
            'custom_fields': {
                '1159524604627932': AsanaPriority.HIGH.value,
                '1199912337121892': '1200218109698442',
                '1199944595440874': 0.1,
                '1200165681182165': '1200198568911550',
                '1199906290951705': teams.CORE_PRODUCT.team_id,
                '1200216708142306': '1200822942218893'
            },
            'notes': ('Previous Asana Task: https://PREV\n\n'
                        'Root Asana Task: https://ROOT\n\n'
                        'Sentry Issue URL: https://sentry.io/organizations/panther-labs/issues/c\n\n'
                        'Event Datetime: 2021-07-14T00:10:08.299179Z\n\n'
                        'Customer Impacted: alpha\n\n'
                        'Environment: prod\n\n')
        }

        # Act
        asana_service.create_asana_task_from_sentry_event(sentry_event, 'https://PREV', 'https://ROOT')

        # Assert
        mock_asana_client.tasks.create_task.assert_called_with(expected_result)

    @patch.object(AsanaService, '_get_owning_team')
    def test_create_asana_task_from_sentry_event(
            self,
            mock_get_owning_team: Any
        ) -> None:
        # Arrange
        mock_get_owning_team.return_value = teams.CORE_PRODUCT
        sentry_event = {
            "datetime":"2021-07-14T00:10:08.299179Z",
            "environment":"prod",
            "level": "error",
            "tags":[
                [
                    "customer_name",
                    "alpha"
                ],
                [
                    "server_name",
                    "panther-snapshot-pollers"
                ]
            ],
            "timestamp":1626221408.299179,
            "title":"some-title",
            "url":"https://url.com/a/",
            "web_url":"https://url.com/b/",
            "issue_url":"https://url.com/c/",
        }
        mock_asana_client = MagicMock()
        mock_asana_client.tasks.create_task.return_value = {
            "gid": "12345",
            "resource_type": "project",
            "name": "new project"
        }
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = 'current_eng_sprint_id'
        asana_service._current_release_testing_project_id = 'current_release_testing_project_id'
        expected_result = {
            'name': "some-title",
            'projects': ['current_eng_sprint_id'],
            'custom_fields': {
                '1159524604627932': AsanaPriority.HIGH.value,
                '1199912337121892': '1200218109698442',
                '1199944595440874': 0.1,
                '1200165681182165': '1200198568911550',
                '1199906290951705': teams.CORE_PRODUCT.team_id,
                '1200216708142306': '1200822942218893'
            },
            'notes': ('Sentry Issue URL: https://sentry.io/organizations/panther-labs/issues/c\n\n'
                        'Event Datetime: 2021-07-14T00:10:08.299179Z\n\n'
                        'Customer Impacted: alpha\n\n'
                        'Environment: prod\n\n')
        }

        # Act
        asana_service.create_asana_task_from_sentry_event(sentry_event, None, None)

        # Assert
        mock_asana_client.tasks.create_task.assert_called_with(expected_result)

    @patch.object(AsanaService, '_get_owning_team')
    def test_create_asana_task_from_sentry_event_staging_no_sprint_project(
            self,
            mock_get_owning_team: Any
        ) -> None:
        # Arrange
        mock_get_owning_team.return_value = teams.DETECTIONS
        sentry_event = {
            "datetime":"2021-07-14T00:10:08.299179Z",
            "environment":"staging",
            "level": "warning",
            "tags":[
                [
                    "customer_name",
                    "alpha"
                ],
                [
                    "server_name",
                    "panther-snapshot-pollers"
                ]
            ],
            "timestamp":1626221408.299179,
            "title":"some-title",
            "url":"https://url.com/a/",
            "web_url":"https://url.com/b/",
            "issue_url":"https://url.com/c/",
        }
        mock_asana_client = MagicMock()
        mock_asana_client.tasks.create_task.return_value = {
            "gid": "12345",
            "resource_type": "project",
            "name": "new project"
        }
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = None
        asana_service._current_release_testing_project_id = 'current_release_testing_project_id'
        expected_result = {
            'name': "some-title",
            'projects': ['current_release_testing_project_id', teams.CORE_PRODUCT.backlog_id],
            'custom_fields': {
                '1159524604627932': AsanaPriority.MEDIUM.value,
                '1199912337121892': '1200218109698442',
                '1199944595440874': 0.1,
                '1200165681182165': '1200198568911550',
                '1199906290951705': teams.DETECTIONS.team_id,
                '1200216708142306': '1200822942218893'
            },
            'notes': ('Sentry Issue URL: https://sentry.io/organizations/panther-labs/issues/c\n\n'
                        'Event Datetime: 2021-07-14T00:10:08.299179Z\n\n'
                        'Customer Impacted: alpha\n\n'
                        'Environment: staging\n\n'
                        'Unable to find the sprint project; assigning to core product backlog.\n\n')
        }

        # Act
        asana_service.create_asana_task_from_sentry_event(sentry_event, None, None)

        # Assert
        mock_asana_client.tasks.create_task.assert_called_with(expected_result)

    @patch.object(AsanaService, '_get_owning_team')
    def test_create_asana_task_from_sentry_event_retry_task_creation(
            self,
            mock_get_owning_team: Any
        ) -> None:
        # Arrange
        mock_get_owning_team.return_value = teams.DETECTIONS
        sentry_event = {
            "datetime":"2021-07-14T00:10:08.299179Z",
            "environment":"prod",
            "level": "critical",
            "tags":[
                [
                    "customer_name",
                    "alpha"
                ],
                [
                    "server_name",
                    "panther-snapshot-pollers"
                ]
            ],
            "timestamp":1626221408.299179,
            "title":"some-title",
            "url":"https://url.com/a/",
            "web_url":"https://url.com/b/",
            "issue_url":"https://url.com/c/",
        }
        mock_asana_client = MagicMock()
        mock_asana_client.tasks.create_task.side_effect = [
            AsanaError.InvalidRequestError(
                'Invalid Request: enum_value: Not a recognized ID: some_id'
            ),
            {
                "gid": "12345",
                "resource_type": "project",
                "name": "new project"
            }
        ]
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = 'current_eng_sprint_id'
        asana_service._current_release_testing_project_id = 'current_release_testing_project_id'
        expected_result = {
            'name': "some-title",
            'projects': ['current_eng_sprint_id'],
            'notes': ('Sentry Issue URL: https://sentry.io/organizations/panther-labs/issues/c\n\n'
                        'Event Datetime: 2021-07-14T00:10:08.299179Z\n\n'
                        'Customer Impacted: alpha\n\n'
                        'Environment: prod\n\n'
                        'Unable to create this task with all custom fields filled out. '
                        'Please alert a team member from observability about this message.')
        }

        # Act
        asana_service.create_asana_task_from_sentry_event(sentry_event, None, None)

        # Assert
        mock_asana_client.tasks.create_task.assert_called_with(expected_result)

    @patch.dict(os.environ, _env_vars)
    def test_load_asana_projects(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        mock_asana_client.projects.get_projects.return_value = [
            {
                "gid": "1199906291903396",
                "name": "Template: Sprint",
                "resource_type": "project"
            },
            {
                "gid": "1200031963805016",
                "name": "Template: Release Testing",
                "resource_type": "project"
            },
            {
                "gid": "1199910262482819",
                "name": "Template: Eng Project",
                "resource_type": "project"
            },
            {
                "gid": "1199906407795548",
                "name": "Backlog: Ingestion",
                "resource_type": "project"
            },
            {
                "gid": "1200693863324520",
                "name": "Sprint 08/02 - 08/20",
                "resource_type": "project"
            },
            {
                "gid": "1200693863324521",
                "name": "Eng Sprint 07/20 - 07/26 (old)",
                "resource_type": "project"
            },
            {
                "gid": "1200319127186571",
                "name": "Release Testing: 08/23 - 09/01",
                "resource_type": "project"
            },
            {
                "gid": "1200319127186570",
                "name": "E2E Testing for Release Testing",
                "resource_type": "project"
            },
        ]
        def get_project_side_effect(gid: str) -> Dict[str, Any]:
            project_info_map = {
                '1200693863324520': {
                    "gid": "1200693863324520", # Eng Sprint 08/02 - 08/20
                    "archived": False,
                    "color": "dark-orange",
                    "created_at": "2021-08-01T20:30:30.159Z"
                },
                '1200693863324521': {
                    "gid": "1200693863324521", # Eng Sprint 07/20 - 07/26 (old)
                    "archived": False,
                    "color": "dark-orange",
                    "created_at": "2021-07-19T20:30:30.159Z"
                },
                '1200319127186571': {
                    "gid": "1200319127186571", # Release Testing: 08/23 - 09/01
                    "archived": False,
                    "color": "dark-orange",
                    "created_at": "2021-08-01T10:30:30.159Z"
                }
            }
            if gid in project_info_map:
                return project_info_map[gid]
            return {}

        mock_asana_client.projects.get_project.side_effect = get_project_side_effect
        asana_service = AsanaService(mock_asana_client, False)

        # Act
        asana_service._load_asana_projects()

        # Assert
        self.assertEqual(asana_service._current_eng_sprint_project_id, '1200693863324520')
        self.assertEqual(asana_service._current_release_testing_project_id, '1200319127186571')

    @patch.dict(os.environ, _env_vars)
    def test_get_project_ids_dev(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        asana_service = AsanaService(mock_asana_client, False)
        expected_result = ['dev-project']

        # Act
        result = asana_service._get_project_ids('dev', 'warning', teams.INVESTIGATIONS)

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_project_ids_staging(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = 'current-eng-sprint-id'
        asana_service._current_release_testing_project_id = 'current_release_testing_project_id'
        expected_result = ['current-eng-sprint-id', 'current_release_testing_project_id']

        # Act
        result = asana_service._get_project_ids('staging', 'warning', teams.DETECTIONS)

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_project_ids_prod_non_warning_level(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = 'current-eng-sprint-id'
        asana_service._current_release_testing_project_id = 'current_release_testing_project_id'
        expected_result: List[str] = ['current-eng-sprint-id']

        # Act
        result = asana_service._get_project_ids('prod', 'critical', teams.INGESTION)

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_project_ids_prod_warning_level(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = 'current-eng-sprint-id'
        asana_service._current_release_testing_project_id = 'current_release_testing_project_id'
        expected_result: List[str] = [teams.INGESTION.backlog_id]

        # Act
        result = asana_service._get_project_ids('prod', 'warning', teams.INGESTION)

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_newest_created_project_id(self) -> None:
        # Arrange
        projects = [
            {
                "gid": "123",
                "name": "Mock Eng Sprint 09/13 - 10/01",
                "resource_type": "project"
            },
            {
                "gid": "124",
                "name": "Mock Eng Sprint 10/04 - 10/22",
                "resource_type": "project"
            }
        ]
        mock_asana_client = MagicMock()
        def get_project_side_effect(gid: str) -> Dict[str, Any]:
            if gid == '123':
                return {
                    "gid":"123",
                    "archived":False,
                    "created_at":"2021-09-12T21:59:08.371Z",
                    "current_status":None,
                    "due_on":"2021-10-01",
                    "modified_at":"2021-10-01T19:41:45.407Z",
                    "name":"Mock Eng Sprint 09/13 - 10/01",
                    "owner":{
                        "gid":"1199946235762137",
                        "resource_type":"user"
                    },
                    "public":True,
                    "resource_type":"project",
                    "start_on":None,
                    "team":{
                        "gid":"1199906122285402",
                        "resource_type":"team"
                    },
                    "workspace":{
                        "gid":"1159526352574257",
                        "resource_type":"workspace"
                    }
                }
            if gid == '124':
                return {
                    "gid":"124",
                    "archived":False,
                    "created_at":"2021-10-01T02:33:09.337Z",
                    "current_status":None,
                    "due_on":None,
                    "modified_at":"2021-10-01T17:01:42.395Z",
                    "name":"Mock Eng Sprint 10/04 - 10/22",
                    "owner":{
                        "gid":"1199946235851409",
                        "resource_type":"user"
                    },
                    "public":True,
                    "resource_type":"project",
                    "start_on":None,
                    "team":{
                        "gid":"1199906122285402",
                        "resource_type":"team"
                    },
                    "workspace":{
                        "gid":"1159526352574257",
                        "resource_type":"workspace"
                    }
                }
            return {}
        mock_asana_client.projects.get_project.side_effect = get_project_side_effect
        asana_service = AsanaService(mock_asana_client, False)
        expected_result = '124'

        # Act
        result = asana_service._get_newest_created_project_id(projects)

        # Assert
        self.assertEqual(result, expected_result)
