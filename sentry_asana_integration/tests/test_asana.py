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
        'DEV_ASANA_SENTRY_PROJECT': 'dev-project'
    }
    def test_get_team_lead_id_with_dev_env(self) -> None:
        # Arrange
        mock_client = MagicMock()
        asana_service = AsanaService(mock_client, False)
        expected_result = '1200567447162380'

        # Act
        result = asana_service._get_team_lead_id(AsanaTeam.LOG_PROCESSING, 'dev')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_team_lead_id_with_non_dev_env(self) -> None:
        # Arrange
        mock_client = MagicMock()
        service = AsanaService(mock_client, False)
        expected_result = '1199946235851409'

        # Act
        result = service._get_team_lead_id(AsanaTeam.CORE_INFRA, 'Prod')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_exact_match_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.ANALYTICS

        # Act
        result = AsanaService._get_owning_team('panther-log-router')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_fnmatch_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.CLOUD_SECURITY

        # Act
        result = AsanaService._get_owning_team('panther-remediation-api')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_fnmatch_server_name_2(self) -> None:
        # Arrange
        expected_result = AsanaTeam.LOG_PROCESSING

        # Act
        result = AsanaService._get_owning_team('panther-log-alpha')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_no_match_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.PANTHER_LABS

        # Act
        result = AsanaService._get_owning_team('alpha-beta')

        # Assert
        self.assertEqual(result, expected_result)

    @patch.object(AsanaService, '_get_owning_team')
    @patch.object(AsanaService, '_get_team_lead_id')
    def test_create_asana_task_from_sentry_event(
            self,
            mock_get_team_lead_id: Any,
            mock_get_owning_team: Any
        ) -> None:
        # Arrange
        mock_get_owning_team.return_value = AsanaTeam.PANTHER_LABS
        mock_get_team_lead_id.return_value = 'stub-id'
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
            "url":"https://url.com/a",
            "web_url":"https://url.com/b",
            "issue_url":"https://url.com/c",
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
            'assignee': 'stub-id',
            'name': "some-title",
            'projects': ['current-eng-sprint-id'],
            'notes': 'Sentry Issue URL: https://url.com/a\nEvent Timestamp: 1626221408.299179\nCustomer Impacted: alpha'
        }

        # Act
        asana_service.create_asana_task_from_sentry_event(sentry_event)

        # Assert
        mock_asana_client.tasks.create_task.assert_called_with(expected_result)

    def test_load_asana_projects(self) -> None:
        # Arrange
        mock_asana_client = MagicMock()
        mock_asana_client.projects.get_projects.return_value = [
            {
                "gid": "1199906291903396",
                "name": "Template: Eng Sprint",
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
                "name": "Eng Backlog",
                "resource_type": "project"
            },
            {
                "gid": "1200693863324520",
                "name": "Eng Sprint 08/02 - 08/20",
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
        self.assertEqual(asana_service._backlog_project_id, '1199906407795548')

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
