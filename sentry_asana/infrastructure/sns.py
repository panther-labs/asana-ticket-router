# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import List
import pulumi
import pulumi_aws as aws
from sentry_asana.infrastructure.helpers.observer import sns


class Sns(pulumi.ComponentResource):
    """A Pulumi Component Resource that represents an SNS Topic.

    This resource is an SNS topic that CloudWatch will post message to when errors are detected.
    """

    def __init__(self, name: str, opts: pulumi.ResourceOptions = None):
        super().__init__('SNS', name, None, opts)
        opts = pulumi.ResourceOptions(parent=self)

        ##################################
        # SNS
        ##################################
        self.sns_topic = sns.create_topic(
            name,
            opts
        )

        # Configure subscriptions based on deployment params
        config = pulumi.Config()
        deployment_params = config.get_object('deploymentParams')

        self.topic_arns = sns.configure(
            name,
            self.sns_topic.arn,
            deployment_params,
            opts=pulumi.ResourceOptions(parent=self.sns_topic)
        )

        # Register the SNS Topics
        self.register_outputs({
            f'{name}-sns-topic': self.sns_topic.arn,
            'topic-arns': self.topic_arns
        })

    def get_topic_arns(self) -> List[str]:
        """Get a list of topic arns"""
        return self.topic_arns

    def get_sns_topic(self) -> aws.sns.Topic:
        """Get the sns topic"""
        return self.sns_topic
