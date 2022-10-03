# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import List, Optional, Any
import pulumi_aws as aws
import pulumi
from .globals import LAMBDA_PRODUCER
from .helpers.serverless import lmbda
from .helpers.iam import role
from .helpers.iam.policies import inline
from .helpers.logs import cw
from .helpers.gateway import api
from .queue import Queue
from .sns import Sns


class Producer(pulumi.ComponentResource):
    """A Pulumi Component Resource that represents a Lambda Fn & API Gateway.

    This resource is the Producer which listens for messages from Sentry and puts them onto a queue.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        name: str,
        que: Queue,
        sns: Sns,
        is_debug: str,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__(f'Resources for {name}', name, None, opts)
        opts = (
            pulumi.ResourceOptions(parent=self)
            if opts is None
            else pulumi.ResourceOptions.merge(opts, pulumi.ResourceOptions(parent=self))
        )

        ##################################
        # Constructed ARNs
        ##################################
        region = aws.config.region  # type: ignore
        account = aws.get_caller_identity().account_id
        config = pulumi.Config()
        deployment_params: Any = config.get_object('deploymentParams')

        is_local_dev = 'false'
        dev_env = deployment_params.get('development')
        dd_kms_arn = deployment_params['DevDatadogAPIKMSArn']
        dd_secret_arn = deployment_params['DevDatadogAPISecretArn']
        if dev_env in ['1', 'true', True]:
            is_local_dev = 'true'
        else:
            dd_secret_arn = deployment_params['ProdDatadogAPISecretArn']
            dd_kms_arn = deployment_params['ProdDatadogAPIKMSArn']

        secret_arn = (
            f'arn:aws:secretsmanager:{region}:{account}:secret:Sentry_Asana_Secrets-*'
        )

        ##################################
        # Log Group
        ##################################
        log_group = cw.create_log_group(name=f'/aws/lambda/{name}', opts=opts)

        ##################################
        # IAM Policies
        ##################################
        inline_policies: List[aws.iam.RoleInlinePolicyArgs] = [
            # like the AWSLambdaBasicExecutionRole managed policy, but restricted to just our log group
            inline.add_log_groups(name, log_group),
            inline.add_secretsmanager(name, secret_arn),
            inline.add_sqs_producer(name, que.get_que()),
            inline.add_secretsmanager(f'{name}-datadog', dd_secret_arn),
            inline.add_kms_datadog(f'{name}-datadog', dd_kms_arn),
        ]

        ##################################
        # IAM Roles
        ##################################
        # Create the role for the Lambda to assume
        lambda_role = role.create(name, inline_policies, opts)

        ##################################
        # Serverless (Lambda)
        ##################################

        lambda_function = lmbda.create(
            name=name,
            role_arn=lambda_role.arn,
            opts=opts,
            archive_path=LAMBDA_PRODUCER,
            environment=aws.lambda_.FunctionEnvironmentArgs(
                variables={
                    'DEBUG': is_debug,
                    'IS_LAMBDA': 'true',
                    'DEVELOPMENT': is_local_dev,
                    'SECRET_NAME': 'Sentry_Asana_Secrets',
                    'QUEUE_URL': que.get_que().url.apply(lambda url: url),
                    'DD_ENV': 'hosted-ops',
                    'DD_API_KEY_SECRET_ARN': dd_secret_arn,
                }
            ),
        )

        ##################################
        # CloudWatch
        ##################################
        # The producer will trigger an alarm if a single error occurs.
        cw.create_alarm_for_lambda(
            name,
            lambda_function.name,
            sns.get_topic_arns(),
            opts=pulumi.ResourceOptions(parent=lambda_function),
        )

        ##################################
        # Permissions
        ##################################
        # Give API Gateway permissions to invoke the Lambda
        lmbda.add_invoke_permission(name, lambda_function.name, opts)

        ##################################
        # API Gateway
        ##################################
        apigw = api.create(name, lambda_function.invoke_arn, opts)

        # Register the endpoint
        self.apigw_endpoint = apigw.api_endpoint
        self.register_outputs({'apigw_endpoint': self.apigw_endpoint})
