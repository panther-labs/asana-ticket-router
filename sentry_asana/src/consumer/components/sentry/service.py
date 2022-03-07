# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import List, Optional, Dict
from logging import Logger
from common.components.serializer.service import SerializerService
from ..requests.service import RequestsService


class SentryService:
    """Sentry Service"""

    def __init__(
        self,
        logger: Logger,
        client: RequestsService,
        serializer: SerializerService,
        bearer: str
    ):
        self._logger = logger
        self._client = client
        self._serializer = serializer
        self._bearer = bearer

    async def find_by_id(self, issue_id: str) -> Dict:
        """Find a Sentry issue details by its issue_id"""
        self._logger.info('Fetching sentry issue details: %s', issue_id)
        response = await self._client.request(
            'GET',
            f'https://sentry.io/api/0/issues/{issue_id}/',
            headers={
                'Authorization': f'Bearer {self._bearer}',
                'Content-Type': 'application/json'
            },
        )
        response.raise_for_status()
        return await response.json(loads=self._serializer.parse)

    async def add_link(self, issue_id: str, asana_task_id: str) -> Dict:
        """Link an asana task Id to a Sentry issue"""
        self._logger.info('Adding asana link to issue: %s', issue_id)
        response = await self._client.request(
            'POST',
            f'https://sentry.io/api/0/issues/{issue_id}/plugins/asana/link/',
            headers={
                'Authorization': f'Bearer {self._bearer}',
                'Content-Type': 'application/json'
            },
            data=self._serializer.stringify({
                'issue_id': asana_task_id,
                'comment': 'Linked by the Sentry-Asana automation'
            })
        )
        response.raise_for_status()
        return await response.json(loads=self._serializer.parse)

    async def get_sentry_asana_link(self, issue_id: str) -> Optional[str]:
        """Gets an asana link from a sentry issue"""

        # Terminate on exception. We _must_ be able to fetch
        # the original sentry issue.
        issue = await self.find_by_id(issue_id)

        plugins: Optional[List[Dict]] = issue.get('pluginIssues', None)
        if plugins is None:
            msg = f'Could not find any plugins for issue: ({issue_id})'
            self._logger.error(msg)
            raise ValueError(msg)

        asana_issue: Optional[Dict] = next(
            (issue for issue in plugins if issue.get('id', '') == 'asana'), None)
        if asana_issue is None:
            msg = f'No asana plugin found for issue: ({issue_id})'
            self._logger.error(msg)
            raise ValueError(msg)

        asana_link: Optional[str] = asana_issue.get(
            'issue', {}).get('url', None)

        if asana_link is None:
            # It is acceptable that we don't find an asana link in the sentry issue
            self._logger.warning('No asana link found for issue: %s', issue_id)
            return None

        return asana_link
