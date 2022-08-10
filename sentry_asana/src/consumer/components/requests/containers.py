# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# pylint: disable=no-member
# mypy: ignore-errors
from dependency_injector import containers, providers
from . import service


class RequestsContainer(containers.DeclarativeContainer):
    """Requests Container"""

    logger = providers.Dependency()
    serializer = providers.Dependency()
    session = providers.Dependency(default=None)

    requests_service = providers.Singleton(
        service.RequestsService, logger=logger, session=session
    )
