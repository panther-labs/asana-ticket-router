# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# mypy: ignore-errors

from dependency_injector import containers, providers
from . import service


class EntitiesContainer(containers.DeclarativeContainer):
    """Entities Container"""

    logger = providers.Dependency()
    teams_service = providers.Singleton(
        service.TeamService,
        logger=logger,
    )
