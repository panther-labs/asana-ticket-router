# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import json
import pulumi_aws as aws


def add_log_groups(
    name: str, log_group: aws.cloudwatch.LogGroup
) -> aws.iam.RoleInlinePolicyArgs:
    """Create an inline policy for Log Group access"""

    return aws.iam.RoleInlinePolicyArgs(
        name=f'{name}-WriteLogs',
        policy=log_group.arn.apply(
            lambda arn: json.dumps(
                {
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            'Resource': [arn, f'{arn}:log-stream:*'],
                        }
                    ],
                }
            ),
        ),
    )


def add_secretsmanager(name: str, secret_arn: str) -> aws.iam.RoleInlinePolicyArgs:
    """Create an inline policy for SecretManager access"""
    return aws.iam.RoleInlinePolicyArgs(
        name=f'{name}-GetSecret',
        policy=json.dumps(
            {
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Action': 'secretsmanager:GetSecretValue',
                        'Resource': secret_arn,
                    }
                ],
            }
        ),
    )


def add_sqs_consumer(name: str, que: aws.sqs.Queue) -> aws.iam.RoleInlinePolicyArgs:
    """Create an inline policy for SQS consumption"""
    return aws.iam.RoleInlinePolicyArgs(
        name=f'{name}-inline-sqs-policy',
        policy=que.arn.apply(
            lambda arn: json.dumps(
                {
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'sqs:ReceiveMessage',
                                'sqs:DeleteMessage',
                                'sqs:GetQueueAttributes',
                            ],
                            'Resource': arn,
                        }
                    ],
                }
            )
        ),
    )


def add_sqs_producer(name: str, que: aws.sqs.Queue) -> aws.iam.RoleInlinePolicyArgs:
    """Create an inline policy for SQS producer"""
    return aws.iam.RoleInlinePolicyArgs(
        name=f'{name}-inline-sqs-policy',
        policy=que.arn.apply(
            lambda arn: json.dumps(
                {
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'sqs:SendMessage',
                                'sqs:SendMessageBatch',
                            ],
                            'Resource': arn,
                        }
                    ],
                }
            )
        ),
    )
