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
        region = aws.config.region  # type: ignore
        account = aws.get_caller_identity().account_id
        config = pulumi.Config()
        stack_name = pulumi.get_stack()
        handler_lambda_name = f'{stack_name}-handler'
        deployment_params = config.get_object('deploymentParams')

        log_group_arn = f'arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{handler_lambda_name}'
        inline_policies: List[aws.iam.RoleInlinePolicyArgs] = [
            # like the AWSLambdaBasicExecutionRole managed policy, but restricted to just our log group
            aws.iam.RoleInlinePolicyArgs(name=f'{stack_name}-WriteLogs', policy=json.dumps({
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
        secret_arn = f'arn:aws:secretsmanager:{region}:{account}:secret:Sentry_Asana_Secrets-*'
        inline_policies.append(
            aws.iam.RoleInlinePolicyArgs(name=f'{stack_name}-GetSecret', policy=json.dumps({
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
            f'{stack_name}-lambda-role',
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

        is_local_dev = False
        if deployment_params and 'development' in deployment_params:
            dev_env = deployment_params.get('development')
            if dev_env in ['1', 'true', True]:
                is_local_dev = True

        # Create the lambda to execute
        lambda_function = aws.lambda_.Function(
            f'{stack_name}-handler-function',
            code=pulumi.AssetArchive({
                '.': pulumi.FileArchive(lambda_deployment_pkg_dir),
            }),
            name=handler_lambda_name,
            environment={
                'variables': {
                    'SECRET_NAME': 'Sentry_Asana_Secrets',
                    'ASANA_ENGINEERING_TEAM_ID': '1199906122285402',
                    'ASANA_PANTHER_LABS_WORKSPACE_ID': '1159526352574257',
                    # Asana ID for 'Test Project (Sentry-Asana integration work)'
                    'DEV_ASANA_SENTRY_PROJECT': '1200611106362920',
                    'RELEASE_TESTING_PORTFOLIO': '1199961111326835',
                    'RELEASE_TESTING_PORTFOLIO_DEV': '1201700591175658',
                    'DEVELOPMENT': is_local_dev
                }
            },
            runtime='python3.9',
            architectures=['arm64'],
            role=lambda_role.arn,
            handler='src.handler.handler',
            description='The handler function for the Sentry-Asana integration service',
            timeout=180,
            opts=pulumi.ResourceOptions(parent=self),
        )

        default_sns_topic = aws.sns.Topic(
            f'{stack_name}-default-sns-topic',
            name=f'{stack_name}-default-sns-topic',
            display_name=f'{stack_name}-default-sns-topic',
            opts=pulumi.ResourceOptions(parent=self),
        )
        topic_arns = [default_sns_topic.arn]
        if deployment_params and 'metricAlarmActionsArns' in deployment_params:
            topic_arns.extend(
                list(deployment_params.get('metricAlarmActionsArns')))

        if deployment_params and 'snsTopicSubscriptionEmailAddresses' in deployment_params:
            for itr, email_address in enumerate(list(deployment_params.get('snsTopicSubscriptionEmailAddresses'))):
                aws.sns.TopicSubscription(
                    f'{stack_name}-sns-topic-{itr + 1}-subscription',
                    endpoint=email_address,
                    protocol='email',
                    topic=default_sns_topic.arn,
                    opts=pulumi.ResourceOptions(parent=default_sns_topic),
                )
        else:
            aws.sns.TopicSubscription(
                f'{stack_name}-sns-topic-fallback-subscription',
                endpoint='eng-core-infra@runpanther.io',
                protocol='email',
                topic=default_sns_topic.arn,
                opts=pulumi.ResourceOptions(parent=default_sns_topic),
            )

        aws.cloudwatch.MetricAlarm(
            f'{stack_name}-lambda-error-metric-alarm',
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
            alarm_description=f'Sentry Asana Automation Error - {handler_lambda_name} Lambda function encountered an error',
            alarm_actions=topic_arns,
            dimensions={
                'FunctionName': handler_lambda_name
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Give API Gateway permissions to invoke the Lambda
        aws.lambda_.Permission(
            f'{stack_name}-apigw-lambda-invoke-permission',
            action='lambda:InvokeFunction',
            function=lambda_function.name,
            principal='apigateway.amazonaws.com',
            opts=pulumi.ResourceOptions(parent=self),
        )

        apigw = aws.apigatewayv2.Api(
            f'{stack_name}-api',
            protocol_type='HTTP',
            route_key='POST /',
            target=lambda_function.invoke_arn,
            opts=pulumi.ResourceOptions(parent=self),
        )
        self.apigw_endpoint = apigw.api_endpoint
        self.register_outputs({
            'apigw_endpoint': self.apigw_endpoint
        })
