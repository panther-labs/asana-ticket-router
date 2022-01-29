# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import os
import json

from unittest import TestCase
from unittest.mock import MagicMock

from ..src.service.sentry_service import SentryService

SENTRY_ISSUE = os.path.join(os.path.dirname(
    __file__), 'test_data', 'sentry_issue.json')


class TestAsanaService(TestCase):
    """Unit Testing Class for AsanaService"""
    _env_vars = {
        'DEV_ASANA_SENTRY_PROJECT': 'dev-project'
    }

    def setUp(self) -> None:
        """Pre-setup that is ran before each test

        We load our example JSON payload from a file
        """
        with open(SENTRY_ISSUE, encoding='utf-8') as file:
            sentry_issue = json.load(file)
            self._sentry_issue = sentry_issue

    def test_get_asana_link_from_sentry_issue_success(
        self,
    ) -> None:
        # Arrange
        mock_sentry_client = MagicMock()
        # Set to a real payload
        mock_sentry_client.find_by_id.return_value = self._sentry_issue
        sentry_service = SentryService(mock_sentry_client)

        # Act
        asana_link = sentry_service.get_sentry_asana_link('1201413464115989')

        # Assert
        mock_sentry_client.find_by_id.assert_called_with('1201413464115989')
        assert asana_link == 'https://app.asana.com/0/0/1201413554245508'

    def test_get_asana_link_from_sentry_issue_fail(
        self,
    ) -> None:
        # Arrange
        mock_sentry_client = MagicMock()
        # Set to invalid data. The function should not have errors
        mock_sentry_client.find_by_id.return_value = None
        sentry_service = SentryService(mock_sentry_client)

        # Act
        asana_link = sentry_service.get_sentry_asana_link('1201413464115989')

        # Assert
        mock_sentry_client.find_by_id.assert_called_with('1201413464115989')
        assert asana_link is None

    def test_add_asana_link_to_issue_success(self) -> None:
        # Arrange
        mock_sentry_client = MagicMock()

        # Set to truthy payload
        mock_sentry_client.add_asana_link_to_issue.return_value = {
            'foo': 'bar'}
        sentry_service = SentryService(mock_sentry_client)

        # Act
        success = sentry_service.add_asana_link_to_issue(
            'issue_id', 'asana_task_id')
        # Assert
        mock_sentry_client.add_asana_link_to_issue.assert_called_with(
            'issue_id', 'asana_task_id')
        assert success is True

    def test_add_asana_link_to_issue_fail(self) -> None:
        # Arrange
        mock_sentry_client = MagicMock()

        # Set to falsy payload
        mock_sentry_client.add_asana_link_to_issue.return_value = None
        sentry_service = SentryService(mock_sentry_client)

        # Act
        success = sentry_service.add_asana_link_to_issue(
            'issue_id', 'asana_task_id')
        # Assert
        mock_sentry_client.add_asana_link_to_issue.assert_called_with(
            'issue_id', 'asana_task_id')
        assert success is False
