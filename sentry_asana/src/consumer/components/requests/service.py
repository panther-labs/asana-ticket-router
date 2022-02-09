# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from asyncio import AbstractEventLoop
from typing import Callable, Any
from logging import Logger
from functools import partial
from requests import Response


class RequestsService:
    """HTTP Requests Service"""

    def __init__(
        self,
        loop: Callable[[], AbstractEventLoop],
        logger: Logger,
        client: Any,
    ):
        self._loop = loop
        self._logger = logger
        self._client = client

    async def request(self, *args: Any, **kwargs: Any) -> Response:
        """Make a request"""
        self._logger.debug("Dispatching request")
        return await self._loop().run_in_executor(
            None,
            partial(
                self._client.request,
                *args,
                **kwargs
            )
        )
