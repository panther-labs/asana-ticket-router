# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from asyncio import AbstractEventLoop
from typing import Dict, Callable
from logging import Logger
from functools import partial
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_secretsmanager.type_defs import GetSecretValueResponseTypeDef
from ..serializer.service import SerializerService


class SecretsManagerService:
    """SecretsManager Service"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        loop: Callable[[], AbstractEventLoop],
        logger: Logger,
        client: SecretsManagerClient,
        secret_name: str,
        serializer: SerializerService,
    ):
        self._loop = loop
        self._logger = logger
        self._client = client
        self._secret_name = secret_name
        self._serializer = serializer

    async def get_secret_string(self) -> Dict[str, str]:
        """Get the SecretString from a secret"""
        self._logger.info("Getting SecretString")
        response = await self._get_secret()
        return self._serializer.parse(response['SecretString'])

    async def _get_secret(self) -> GetSecretValueResponseTypeDef:
        """Get a secret"""
        self._logger.info("Getting AWS Secret")
        return await self._loop().run_in_executor(
            None, partial(self._client.get_secret_value, SecretId=self._secret_name)
        )
