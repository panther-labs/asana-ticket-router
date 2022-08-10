# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import List
import pulumi_aws as aws
import pulumi


def create_log_group(
    name: str, opts: pulumi.ResourceOptions
) -> aws.cloudwatch.LogGroup:
    """Create a new LogGroup"""
    return aws.cloudwatch.LogGroup(
        name=name, resource_name=name, retention_in_days=0, opts=opts
    )


def create_alarm_for_lambda(
    name: str, lambda_name: str, topic_arns: List[str], opts: pulumi.ResourceOptions
) -> aws.cloudwatch.MetricAlarm:
    """Create a new CW Metric Alarm for Lambda"""
    return aws.cloudwatch.MetricAlarm(
        resource_name=f'{name}-lambda-alarm',
        comparison_operator='GreaterThanOrEqualToThreshold',
        evaluation_periods=1,
        datapoints_to_alarm=1,
        actions_enabled=True,
        metric_name='Errors',
        namespace='AWS/Lambda',
        period=60,
        statistic='Maximum',
        threshold=1,
        treat_missing_data='missing',
        alarm_description='Sentry Asana Lambda function encountered an error',
        alarm_actions=topic_arns,
        dimensions={'FunctionName': lambda_name},
        opts=opts,
    )


def create_alarm_for_sqs(
    name: str, queue_name: str, topic_arns: List[str], opts: pulumi.ResourceOptions
) -> aws.cloudwatch.MetricAlarm:
    """Create a new CW Threshold Alarm for SQS"""
    return aws.cloudwatch.MetricAlarm(
        resource_name=f'{name}-sqs-alarm',
        comparison_operator='GreaterThanThreshold',
        evaluation_periods=1,
        datapoints_to_alarm=1,
        actions_enabled=True,
        metric_name='ApproximateNumberOfMessagesVisible',
        namespace='AWS/SQS',
        period=60,
        statistic='Sum',
        threshold=0,
        treat_missing_data='missing',
        alarm_description='Sentry Asana SQS has messages. Please investigate and re-queue.',
        alarm_actions=topic_arns,
        dimensions={'QueueName': queue_name},
        opts=opts,
    )
