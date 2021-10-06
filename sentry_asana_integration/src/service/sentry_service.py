# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

from typing import Any, Dict
import requests

from .secrets_service import SecretKey, SecretsService
from ..util.logger import get_logger



class SentryService:
    """Service class that interacts with Sentry API

    Attributes:
        _secrets_service: A Secrets Service object; used to retrieve the Sentry PAT from secrets manager.
        _logger: A reference to a Logger object.
    """
    def __init__(self, secrets_service: SecretsService) -> None:
        self._secrets_service = secrets_service
        self._logger = get_logger()

    def link_issue_to_asana_task(self, sentry_event: Dict[str, Any], asana_task_id: str) -> bool:
        """Links Sentry issue to Asana task

        Using an undocumented Sentry API, this function links an Asana task this service has
        created with the Sentry event that triggered the service.

        Args:
            sentry_event: A Dict representing the body contained in the Sentry event.
            asana_task_id: A string representing the 'gid' of the Asana task that
              was created for this issue.

        Returns:
            A bool representing whether the API call to link the issue with the task
              was successful.
        """
        issue_url = sentry_event['issue_url']
        if issue_url[-1] == '/':
            issue_url = issue_url[:len(issue_url) - 1]
        issue_id = issue_url.split('/')[-1]
        response = requests.post(
            url=f'https://sentry.io/api/0/issues/{issue_id}/plugins/asana/link/',
            headers={
                'Authorization': f'Bearer {self._secrets_service.get_secret_value(SecretKey.SENTRY_PAT)}',
                'Content-Type': 'application/json'
            },
            data={
                'issue_id': asana_task_id,
                'comment': 'Linked by the Sentry-Asana automation'
            }
        )
        if response.status_code != 200:
            self._logger.warning('Linking failed. Non-200 response returned: %s', response)
            return False
        return True
