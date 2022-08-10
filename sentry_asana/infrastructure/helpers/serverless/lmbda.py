# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import Optional
import pulumi_aws as aws
import pulumi

from sentry_asana.infrastructure.globals import (
    LAMBDA_TIMEOUT_SECONDS,
    LAMBDA_ARCHITECTURE,
    LAMBDA_RUNTIME,
    LAMBDA_FILE,
    LAMBDA_HANDLER,
    BATCH_SECONDS,
)
from sentry_asana.infrastructure.helpers.serverless.util import create_lambda_package


def create(
    name: str,
    role_arn: str,
    archive_path: str,
    opts: pulumi.ResourceOptions,
    environment: Optional[aws.lambda_.FunctionEnvironmentArgs] = None,
) -> aws.lambda_.Function:
    """Create a new AWS Lambda"""
    folder = name.split('-')[-1]
    return aws.lambda_.Function(
        resource_name=name,
        name=name,
        code=pulumi.AssetArchive(
            {
                '.': pulumi.FileArchive(create_lambda_package(archive_path)),
            }
        ),
        environment=environment,
        runtime=LAMBDA_RUNTIME,
        architectures=[LAMBDA_ARCHITECTURE],
        role=role_arn,
        handler=f'{folder}.{LAMBDA_FILE}.{LAMBDA_HANDLER}',
        description=f'The {name} in the Sentry-Asana service',
        timeout=LAMBDA_TIMEOUT_SECONDS,
        opts=opts,
    )


def add_invoke_permission(
    name: str, lambda_name: str, opts: pulumi.ResourceOptions
) -> aws.lambda_.Permission:
    """Add API Gateway invoke permissions to lambda"""
    return aws.lambda_.Permission(
        resource_name=f'{name}-apigw-invoke-lamda-permission',
        action='lambda:InvokeFunction',
        function=lambda_name,
        principal='apigateway.amazonaws.com',
        opts=opts,
    )


def add_sqs_permission(
    name: str, lambda_name: str, opts: pulumi.ResourceOptions
) -> aws.lambda_.Permission:
    """Add SQS invoke permissions to lambda"""
    return aws.lambda_.Permission(
        resource_name=f'{name}-sqs-lambda-invoke-permission',
        action='lambda:InvokeFunction',
        function=lambda_name,
        principal='sqs.amazonaws.com',
        opts=opts,
    )


def add_sqs_event_mapping(
    name: str, que: aws.sqs.Queue, lambda_arn: str, opts: pulumi.ResourceOptions
) -> aws.lambda_.EventSourceMapping:
    """Add an SQS event mapping to a lambda"""
    return aws.lambda_.EventSourceMapping(
        resource_name=f'{name}-event-source-mapping',
        event_source_arn=que.arn.apply(lambda arn: arn),
        function_name=lambda_arn,
        maximum_batching_window_in_seconds=BATCH_SECONDS,
        # Set to allow partial retry of failed batch messages
        function_response_types=['ReportBatchItemFailures'],
        opts=opts,
    )
