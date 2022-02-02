# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import json
from typing import Any, Dict, Optional

import requests

from consumer.util.logger import get_logger
from consumer.service.secrets_service import SecretKey, SecretsService


class SentryClient:
    """Service class that interacts with Sentry API

    Attributes:
        _secrets_service: A Secrets Service object; used to retrieve the Sentry PAT from secrets manager.
        _client: A requestor client to dispatch HTTP requests
        _logger: A reference to a Logger object.
    """

    def __init__(self, secrets_service: SecretsService, client: Any) -> None:
        self._secrets_service = secrets_service
        self._client = client
        self._logger = get_logger()

    def find_by_id(self, issue_id: str) -> Any:
        """Find a Sentry issue by its id.

        Args:
            issue_id: A string representing a sentry issue id

        Returns:
            The JSON payload of the response
        """
        try:
            response = self._client.get(
                url=f'https://sentry.io/api/0/issues/{issue_id}/',
                headers={
                    'Authorization': f'Bearer {self._secrets_service.get_secret_value(SecretKey.SENTRY_PAT)}',
                    'Content-Type': 'application/json'
                },
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as excpt:
            self._logger.error(
                'Unknown error fetching sentry issue: %s', excpt)
            return None

    def add_asana_link_to_issue(self, issue_id: str, asana_task_id: str) -> Any:
        """Link an asana task Id to a Sentry issue.

        Using an undocumented Sentry API, this function links an Asana task this service has
        created with the Sentry event that triggered the service.

        Args:
            issue_id: A string representing a sentry issue id
            asana_task_id: A string representing the asana task id
        Returns:
            The JSON payload of the response
        """
        try:
            response = self._client.post(
                url=f'https://sentry.io/api/0/issues/{issue_id}/plugins/asana/link/',
                headers={
                    'Authorization': f'Bearer {self._secrets_service.get_secret_value(SecretKey.SENTRY_PAT)}',
                    'Content-Type': 'application/json'
                },
                data=json.dumps({
                    'issue_id': asana_task_id,
                    'comment': 'Linked by the Sentry-Asana automation'
                })
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as excpt:
            self._logger.error('Unknown error adding asana link: %s', excpt)
            return None


class SentryService:
    """Service class that interacts with Sentry API

    Attributes:
        _sentry_client: A SentryClient object; used to dispatch requests to the Sentry API
        _logger: A reference to a Logger object.
    """

    def __init__(self, sentry_client: SentryClient) -> None:
        self._sentry_client = sentry_client
        self._logger = get_logger()

    def get_sentry_asana_link(self, issue_id: str) -> Optional[str]:
        """Fetches a sentry issue

        This function fetches a sentry issue specified by the given issue_id

        Args:
            issue_id: The string representing the id of the sentry issue

        Returns:
            The asana link as a str or None if not found
        """
        issue = self._sentry_client.find_by_id(issue_id)
        if issue is None:
            return None

        plugin_issues = issue.get('pluginIssues', [])
        # Extract the first asana plugin issue we find in the list
        asana_issue: Dict[str, Any] = next(
            (issue for issue in plugin_issues if issue.get('id') == 'asana'), {})
        if not asana_issue:
            self._logger.error('No asana plugin found for issue: %s', issue_id)
            return None

        asana_link = asana_issue.get('issue', {}).get('url', None)
        if not asana_link:
            self._logger.warning('No asana link found for issue: %s', issue_id)
            return None
        return asana_link

    def add_asana_link_to_issue(self, issue_id: str, asana_task_id: str) -> bool:
        """Links Sentry issue to Asana task

        Args:
            issue_id: A string representing a sentry issue id
            asana_task_id: A string representing the 'gid' of the Asana task that
              was created for this issue.

        Returns:
            A bool representing whether the API call to link the issue with the task
              was successful.
        """
        response = self._sentry_client.add_asana_link_to_issue(
            issue_id, asana_task_id)
        if response is None:
            return False
        return True
