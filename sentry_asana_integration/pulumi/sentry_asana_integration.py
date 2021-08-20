# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import json
from typing import List

import pulumi_aws as aws

import pulumi


class SentryAsanaIntegration(pulumi.ComponentResource):
    """A Pulumi Component Resource that represents a Lambda Fn & API Gateway that enable Sentry -> Asana integration."""
    def __init__(self, name: str, lambda_deployment_pkg_dir: str, opts: pulumi.ResourceOptions = None):
        super().__init__('panther:internal:integration', name, None, opts)
        handler_lambda_name = f'{name}-handler'
        region = aws.config.region # type: ignore
        account = aws.get_caller_identity().account_id

        log_group_arn = f'arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{handler_lambda_name}'
        inline_policies: List[aws.iam.RoleInlinePolicyArgs] = [
            # like the AWSLambdaBasicExecutionRole managed policy, but restricted to just our log group
            aws.iam.RoleInlinePolicyArgs(name=f'{name}-WriteLogs', policy=json.dumps({
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Action': [
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents'
                            ],
                            'Resource': [
                                log_group_arn,
                                f'{log_group_arn}:log-stream:*'
                            ]
                        }
                    ],
                })
            )
        ]

        # This secret is not created dynamically; it needs to be manually created in the deployment account
        secret_arn = f'arn:aws:secretsmanager:{region}:{account}:secret:integration/sentry-asana-*'
        inline_policies.append(
            aws.iam.RoleInlinePolicyArgs(name=f'{name}-GetSecret', policy=json.dumps({
                    'Statement': [
                        {
                            'Effect': 'Allow',
                            'Action': 'secretsmanager:GetSecretValue',
                            'Resource': secret_arn
                        }
                    ],
                })
            )
        )

        # Create the role for the Lambda to assume
        lambda_role = aws.iam.Role(
            f'{name}-lambda-role',
            assume_role_policy=json.dumps({
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'sts:AssumeRole',
                    'Principal': {
                        'Service': 'lambda.amazonaws.com',
                    },
                    'Effect': 'Allow',
                }]
            }),
            inline_policies=inline_policies,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Create the lambda to execute
        lambda_function = aws.lambda_.Function(
            f'{name}-handler-function',
            code=pulumi.AssetArchive({
                '.': pulumi.FileArchive(lambda_deployment_pkg_dir),
            }),
            name=handler_lambda_name,
            environment={
                'variables': {
                    'SECRET_NAME': 'integration/sentry-asana',
                    'ASANA_ENGINEERING_TEAM_ID': '1199906122285402',
                    'ASANA_PANTHER_LABS_WORKSPACE_ID': '1159526352574257',
                    'DEV_ASANA_SENTRY_PROJECT': '1200611106362920', # Asana ID for 'Test Project (Sentry-Asana integration work)'
                    'DEV_TEAM_LEAD_ID': '1200567447162380' # Asana ID for Yusuf Akhtar
                }
            },
            runtime='python3.7',
            role=lambda_role.arn,
            handler='src.handler.handler',
            description='The handler function for the Sentry-Asana integration service',
            timeout=30,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Give API Gateway permissions to invoke the Lambda
        aws.lambda_.Permission(
            f'{name}-apigw-lambda-invoke-permission',
            action='lambda:InvokeFunction',
            function=lambda_function.name,
            principal='apigateway.amazonaws.com',
            opts=pulumi.ResourceOptions(parent=self),
        )

        apigw = aws.apigatewayv2.Api(
            f'{name}-api',
            protocol_type='HTTP',
            route_key='POST /',
            target=lambda_function.invoke_arn,
            opts=pulumi.ResourceOptions(parent=self),
        )
        self.apigw_endpoint = apigw.api_endpoint
        self.register_outputs({
            'apigw_endpoint': self.apigw_endpoint
        })
