# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from asyncio import AbstractEventLoop
from typing import Callable
from logging import Logger
from functools import partial
from mypy_boto3_sqs import SQSClient
from mypy_boto3_sqs.type_defs import SendMessageResultTypeDef


class QueueService:
    """Message Service"""

    def __init__(
        self,
        loop: Callable[[], AbstractEventLoop],
        logger: Logger,
        client: SQSClient,
        queue_url: str,
    ):
        self._loop = loop
        self._logger = logger
        self._client = client
        self._queue_url = queue_url

    async def put(self, message: str, alert_type: str) -> SendMessageResultTypeDef:
        """Put a message onto a queue"""
        self._logger.info("Sending to queue")
        return await self._loop().run_in_executor(
            None,
            partial(
                self._client.send_message,
                QueueUrl=self._queue_url,
                MessageBody=message,
                MessageAttributes={
                    'AlertType': {'StringValue': alert_type, 'DataType': 'String'}
                },
            ),
        )
