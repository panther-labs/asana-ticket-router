# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import base64
import json
import os
from enum import Enum
from typing import Any, Dict, List


class SecretKey(Enum):
    """Enum that defines the secret keys within the SecretsManager secret."""
    ASANA_PAT = 'ASANA_PAT'
    SENTRY_CLIENT_SEC = 'SENTRY_CLIENT_SECRET'

    @staticmethod
    def list_all_secret_keys() -> List[str]:
        """A helper function that returns all the Enum values as a list.

        Returns:
            A list of strings representing all the SecretKey Enum values.
        """
        return list(map(lambda s: s.value, SecretKey))


class SecretsService:
    """Helper class that interacts with AWS Secrets Manager.

    Attributes:
        _secrets_client: A boto3 secretsmanager client object.
        _secrets: A dict containing all the secret key/values needed for the
          Sentry-Asana integration service.
    """
    def __init__(self, secrets_client: Any):
        self._secrets_client = secrets_client
        self._secrets: Dict[str, str] = self.get_secrets_from_secrets_manager()
        expected_secret_keys = SecretKey.list_all_secret_keys()
        if not set(expected_secret_keys).issubset(set(self._secrets.keys())):
            raise KeyError(
                (f"List of expected secrets {expected_secret_keys} is not a subset "
                f"of list of keys within retrieved secret {list(self._secrets.keys())}")
            )

    def get_secrets_from_secrets_manager(self) -> Dict[str, str]:
        """Retrieves all the relevant secrets from AWS Secrets Manager.

        Returns:
            A dict containing all relevant secret key/values.
        """
        secret = {}
        get_secret_value_response = self._secrets_client.get_secret_value(
            SecretId=os.environ.get('SECRET_NAME')
        )
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
        else:
            secret = json.loads(base64.b64decode(get_secret_value_response['SecretBinary']))
        return secret

    def get_secret_value(self, secret_key: SecretKey) -> str:
        """Retrieves the secret value given a key.

        This function assumes that there exists a _secrets class attribute that represents
        a dict containing all the secret key/values needed for this service. This dict
        is loaded during the execution of the SecretsService constructor.

        Args:
            secret_key: A SecretKey Enum representing a key in the _secrets dict.

        Returns:
            A string representing the secret value.
        """
        return self._secrets[secret_key.value]
