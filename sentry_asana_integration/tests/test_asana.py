# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import os
from typing import Any, Dict
from unittest import TestCase
from unittest.mock import MagicMock, patch

from ..src.service.asana_service import AsanaService, AsanaTeam


class TestAsanaService(TestCase):
    """Unit Testing Class for AsanaService"""
    _env_vars = {
        'DEV_ASANA_SENTRY_PROJECT': 'dev-project',
        'CORE_PLATFORM_BACKLOG_PROJECT': 'core-platform-backlog-project'
    }

    def test_get_owning_team_with_exact_match_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.INVESTIGATIONS

        # Act
        result = AsanaService._get_owning_team('panther-log-router')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_fnmatch_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.DETECTIONS

        # Act
        result = AsanaService._get_owning_team('panther-remediation-api')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_fnmatch_server_name_2(self) -> None:
        # Arrange
        expected_result = AsanaTeam.INGESTION

        # Act
        result = AsanaService._get_owning_team('panther-log-alpha')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_no_match_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.CORE_PLATFORM

        # Act
        result = AsanaService._get_owning_team('alpha-beta')

        # Assert
        self.assertEqual(result, expected_result)

    @patch.object(AsanaService, '_get_owning_team')
    def test_create_asana_task_from_sentry_event(
            self,
            mock_get_owning_team: Any
        ) -> None:
        # Arrange
        mock_get_owning_team.return_value = AsanaTeam.CORE_PLATFORM
        sentry_event = {
            "datetime":"2021-07-14T00:10:08.299179Z",
            "environment":"prod",
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
        asana_service._current_eng_sprint_project_id = 'current-eng-sprint-id'
        asana_service._current_dogfooding_project_id = 'current_dogfooding_project_id'
        asana_service._backlog_project_id = 'backlog_project_id'
        expected_result = {
            'name': "some-title",
            'projects': ['current-eng-sprint-id'],
            'custom_fields': {
                '1159524604627932': '1159524604627933',
                '1199912337121892': '1200218109698442',
                '1199944595440874': 0.1,
                '1200165681182165': '1200198568911550',
                '1199906290951705': '1199906290951724',
                '1200216708142306': '1200822942218893'
            },
            'notes': ('Sentry Issue URL: https://sentry.io/organizations/panther-labs/issues/c\n\n'
                        'Event Datetime: 2021-07-14T00:10:08.299179Z\n\nCustomer Impacted: alpha')
        }

        # Act
        asana_service.create_asana_task_from_sentry_event(sentry_event)

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
                "name": "Template: Dogfooding",
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
                "name": "Current Dogfooding",
                "resource_type": "project"
            },
            {
                "gid": "1200319127186570",
                "name": "Old Dogfooding",
                "resource_type": "project"
            },
        ]
        def get_project_side_effect(gid: str) -> Dict[str, Any]:
            project_info_map = {
                '1200693863324520': {
                    "data": {
                        "gid": "1200693863324520", # Eng Sprint 08/02 - 08/20
                        "archived": False,
                        "color": "dark-orange",
                        "created_at": "2021-08-01T20:30:30.159Z"
                    }
                },
                '1200693863324521': {
                    "data": {
                        "gid": "1200693863324521", # Eng Sprint 07/20 - 07/26 (old)
                        "archived": False,
                        "color": "dark-orange",
                        "created_at": "2021-07-19T20:30:30.159Z"
                    }
                },
                '1200319127186571': {
                    "data": {
                        "gid": "1200319127186571", # Current Dogfooding
                        "archived": False,
                        "color": "dark-orange",
                        "created_at": "2021-08-01T10:30:30.159Z"
                    }
                },
                '1200319127186570': {
                    "data": {
                        "gid": "1200319127186570", # Old Dogfooding
                        "archived": False,
                        "color": "dark-orange",
                        "created_at": "2021-07-19T09:30:30.159Z"
                    }
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
        self.assertEqual(asana_service._current_dogfooding_project_id, '1200319127186571')
        self.assertEqual(asana_service._backlog_project_id, 'core-platform-backlog-project')

    @patch.dict(os.environ, _env_vars)
    def test_get_project_ids_dev(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        asana_service = AsanaService(mock_asana_client, False)
        expected_result = ['dev-project']

        # Act
        result = asana_service._get_project_ids('dev')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_project_ids_staging(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = 'current-eng-sprint-id'
        asana_service._current_dogfooding_project_id = 'current_dogfooding_project_id'
        asana_service._backlog_project_id = 'backlog_project_id'
        expected_result = ['current-eng-sprint-id', 'current_dogfooding_project_id']

        # Act
        result = asana_service._get_project_ids('staging')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_project_ids_prod_no_eng_sprint(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        asana_service = AsanaService(mock_asana_client, False)
        asana_service._current_eng_sprint_project_id = None
        asana_service._current_dogfooding_project_id = 'current_dogfooding_project_id'
        asana_service._backlog_project_id = 'backlog_project_id'
        expected_result = ['backlog_project_id']

        # Act
        result = asana_service._get_project_ids('prod')

        # Assert
        self.assertEqual(result, expected_result)
