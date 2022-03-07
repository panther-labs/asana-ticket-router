# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import Any, Optional, AsyncGenerator
from logging import Logger
from contextlib import asynccontextmanager
from aiohttp import ClientSession, ClientResponse


class RequestsService:
    """HTTP Requests Service"""

    def __init__(
        self,
        logger: Logger,
        session: Optional[ClientSession]
    ):
        self._logger = logger
        self._session = session

    @asynccontextmanager
    async def with_session(self) -> AsyncGenerator[None, None]:
        """Session Context"""
        self._logger.debug("Creating http session")
        self._session = ClientSession()
        try:
            yield
        finally:
            self._logger.debug("Closing http session")
            await self._session.close()
            self._session = None

    async def request(self, *args: Any, **kwargs: Any) -> ClientResponse:
        """Make a request"""
        self._logger.debug("Dispatching request")
        if self._session is None:
            raise RuntimeError(
                "No session. Please use the `with_session` helper.")
        return await self._session.request(
            *args,
            **kwargs
        )
