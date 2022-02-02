# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import Any, List
import pulumi_aws as aws
import pulumi


def create_topic(name: str, opts: pulumi.ResourceOptions) -> aws.sns.Topic:
    """Create a new SNS Topic"""
    name = f'{name}-sns-topic'
    return aws.sns.Topic(
        resource_name=name,
        name=name,
        display_name=name,
        opts=opts,
    )


def create_subscription(
    name: str,
    label: str,
    email_address: str,
    topic_arn: str,
    opts: pulumi.ResourceOptions
) -> aws.sns.TopicSubscription:
    """Create a new SNS Subscription"""
    return aws.sns.TopicSubscription(
        resource_name=f'{name}-sns-topic-{label}-subscription',
        endpoint=email_address,
        protocol='email',
        topic=topic_arn,
        opts=opts,
    )


def configure(name: str, sns_topic_arn: str, deployment_params: Any, opts: pulumi.ResourceOptions) -> List[str]:
    """Congigure the SNS Topic with additional parameters specified by the deployment parameters"""
    topic_arns = [sns_topic_arn]

    if deployment_params and deployment_params.get('alarmActionsTopic'):
        topic_arns.extend(
            list(deployment_params.get('alarmActionsTopic')))

    if deployment_params and deployment_params.get('alarmEmailSubscriptions'):
        for itr, email_address in enumerate(list(deployment_params.get('alarmEmailSubscriptions'))):
            create_subscription(
                name,
                str(itr + 1),
                email_address,
                sns_topic_arn,
                opts=opts,
            )

    else:
        create_subscription(
            name,
            'fallback',
            'team-platform-observability@runpanther.io',
            sns_topic_arn,
            opts=opts,
        )

    return topic_arns
