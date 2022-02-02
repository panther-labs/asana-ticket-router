# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import json
from dependency_injector import containers, providers
from . import service


class SerializerContainer(containers.DeclarativeContainer):
    """Serializer Container"""

    serializer_service = providers.Singleton(
        service.SerializerService,
        serialize=json.dumps,
        deserialize=json.loads,
    )
