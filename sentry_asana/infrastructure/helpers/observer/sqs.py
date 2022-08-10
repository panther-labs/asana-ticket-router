# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import json
from typing import Optional
import pulumi_aws as aws
import pulumi
from sentry_asana.infrastructure.globals import SQS_VISIBILITY_TIMEOUT_SECONDS


def create(
    name: str,
    dlq: Optional[aws.sqs.Queue] = None,
    is_dlq: bool = False,
    opts: Optional[pulumi.ResourceOptions] = None,
) -> aws.sqs.Queue:
    """Create a new SQS Queue"""

    return aws.sqs.Queue(
        resource_name=f'{name}-queue-dlq' if is_dlq else f'{name}-queue',
        args=aws.sqs.QueueArgs(
            message_retention_seconds=1209600,  # 14 days is the max
            receive_wait_time_seconds=10,
            # The DLQ at this point is still waiting to be created, therefore we use
            # the 'apply' helper to grab the output at runtime.
            redrive_policy=dlq.arn.apply(
                lambda arn: json.dumps(
                    {
                        "deadLetterTargetArn": arn,
                        "maxReceiveCount": 10,
                    }
                )
            )
            if dlq
            else None,
            visibility_timeout_seconds=SQS_VISIBILITY_TIMEOUT_SECONDS,
        ),
        opts=opts,
    )
