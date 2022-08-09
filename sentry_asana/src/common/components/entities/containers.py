# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
# mypy: ignore-errors
# pylint: disable=no-member

import io
from dependency_injector import containers, providers
from sentry_asana.src.common.components.entities import service


def _wrap_io(param):
    """Return a file-like object.

    For prod, we read from files; but for testing we read from io.StringIOs.
    Do the right thing depending on type.
    """
    if isinstance(param, io.StringIO):
        return param
    # Assume param is a file and open it for read.
    return open(param, "rb")


class EntitiesContainer(containers.DeclarativeContainer):
    """EntitiesContainer"""

    config = providers.Configuration(strict=True)
    teams_service = providers.Singleton(
        service.TeamService,
        team_data=providers.Resource(_wrap_io, config.entities.team_data_file),
    )
