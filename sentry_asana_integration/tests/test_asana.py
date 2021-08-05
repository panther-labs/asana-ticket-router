# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

from unittest import TestCase
from unittest.mock import MagicMock

from ..src.asana import AsanaService, AsanaTeam


class TestAsanaService(TestCase):
    """Unit Testing Class for AsanaService"""
    def test_get_team_lead_id_with_dev_env(self) -> None:
        # Arrange
        mock_client = MagicMock()
        service = AsanaService(mock_client)
        expected_result = '1200567447162380'

        # Act
        result = service.get_team_lead_id(AsanaTeam.LOG_PROCESSING, 'dev')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_team_lead_id_with_non_dev_env(self) -> None:
        # Arrange
        mock_client = MagicMock()
        service = AsanaService(mock_client)
        expected_result = '1199946235851409'

        # Act
        result = service.get_team_lead_id(AsanaTeam.CORE_INFRA, 'Prod')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_exact_match_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.ANALYTICS

        # Act
        result = AsanaService.get_owning_team('panther-log-router')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_fnmatch_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.CLOUD_SECURITY

        # Act
        result = AsanaService.get_owning_team('panther-remediation-api')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_fnmatch_server_name_2(self) -> None:
        # Arrange
        expected_result = AsanaTeam.LOG_PROCESSING

        # Act
        result = AsanaService.get_owning_team('panther-log-alpha')

        # Assert
        self.assertEqual(result, expected_result)

    def test_get_owning_team_with_no_match_server_name(self) -> None:
        # Arrange
        expected_result = AsanaTeam.PANTHER_LABS

        # Act
        result = AsanaService.get_owning_team('alpha-beta')

        # Assert
        self.assertEqual(result, expected_result)
