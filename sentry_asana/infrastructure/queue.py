# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import pulumi
import pulumi_aws as aws
from sentry_asana.infrastructure.helpers.observer import sqs
from .sns import Sns
from .helpers.logs import cw


class Queue(pulumi.ComponentResource):
    """A Pulumi Component Resource that represents a Queue (with implicit DLQ).

    This resource is an SQS queue that a Producer will send data to and for a Consumer to receive data.
    """

    def __init__(self, name: str, sns: Sns, opts: pulumi.ResourceOptions = None):
        super().__init__('Queues', name, None, opts)
        opts = pulumi.ResourceOptions(parent=self)

        ##################################
        # SQS
        ##################################
        # Create DLQ
        self.dlq = sqs.create(
            name, is_dlq=True, opts=pulumi.ResourceOptions(parent=self)
        )

        # Then, create our message queue with the DLQ specified as a redrive policy
        self.que = sqs.create(
            name,
            dlq=self.dlq,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[self.dlq]),
        )

        # Add alarm for the DQL to notify SNS if messages are present
        cw.create_alarm_for_sqs(
            name=name,
            queue_name=self.dlq.name,
            topic_arns=sns.get_topic_arns(),
            opts=pulumi.ResourceOptions(parent=self.dlq, depends_on=[self.dlq]),
        )

        # Register the queues
        self.register_outputs(
            {f'{name}-dlq-arn': self.dlq.arn, f'{name}-arn': self.que.arn}
        )

    def get_que(self) -> aws.sqs.Queue:
        """Get the message queue from the resource"""
        return self.que
