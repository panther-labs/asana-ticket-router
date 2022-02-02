# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import List, Optional
import pulumi_aws as aws
import pulumi
from .globals import LAMBDA_CONSUMER
from .helpers.serverless import lmbda
from .helpers.iam import role
from .helpers.iam.policies import inline
from .helpers.logs import cw
from .queue import Queue
from .sns import Sns


class Consumer(pulumi.ComponentResource):
    """A Pulumi Component Resource that represents a Lambda Fn.

    This resource is the Consumer which listens for messages from SQS and creates tasks in Asana.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, name: str, que: Queue, sns: Sns, is_debug: str, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(f'Resources for {name}', name, None, opts)
        opts = pulumi.ResourceOptions(parent=self) if opts is None else pulumi.ResourceOptions.merge(
            opts, pulumi.ResourceOptions(parent=self))

        ##################################
        # Constructed ARNs
        #
        # These are resources which are not
        # controlled by this repository
        ##################################
        region = aws.config.region  # type: ignore
        account = aws.get_caller_identity().account_id
        secret_arn = f'arn:aws:secretsmanager:{region}:{account}:secret:Sentry_Asana_Secrets-*'

        ##################################
        # Log Group
        ##################################
        log_group = cw.create_log_group(
            name=f'/aws/lambda/{name}',
            opts=opts
        )

        ##################################
        # IAM Policies
        ##################################
        inline_policies: List[aws.iam.RoleInlinePolicyArgs] = [
            # like the AWSLambdaBasicExecutionRole managed policy, but restricted to just our log group
            inline.add_log_groups(
                name,
                log_group
            ),
            inline.add_secretsmanager(
                name,
                secret_arn
            ),
            inline.add_sqs_consumer(
                name,
                que.get_que()
            )
        ]

        ##################################
        # IAM Roles
        ##################################
        # Create the role for the Lambda to assume
        lambda_role = role.create(
            name,
            inline_policies,
            opts
        )

        ##################################
        # Serverless (Lambda)
        ##################################
        config = pulumi.Config()
        deployment_params = config.get_object('deploymentParams')
        is_local_dev = 'false'
        if deployment_params and 'development' in deployment_params:
            dev_env = deployment_params.get('development')
            if dev_env in ['1', 'true', True]:
                is_local_dev = 'true'

        lambda_function = lmbda.create(
            name=name,
            role_arn=lambda_role.arn,
            opts=opts,
            archive_path=LAMBDA_CONSUMER,
            environment=aws.lambda_.FunctionEnvironmentArgs(
                variables={
                    'DEBUG': is_debug,
                    'IS_LAMBDA': 'true',
                    'DEVELOPMENT': is_local_dev,
                    'SECRET_NAME': 'Sentry_Asana_Secrets',
                    # Asana ID for 'Test Project (Sentry-Asana integration work)'
                    'DEV_ASANA_SENTRY_PROJECT': '1200611106362920',
                    'RELEASE_TESTING_PORTFOLIO': '1199961111326835',
                    'RELEASE_TESTING_PORTFOLIO_DEV': '1201700591175658'
                }
            )
        )

        ##################################
        # CloudWatch
        ##################################
        cw.create_alarm_for_lambda(
            name,
            lambda_function.name,
            sns.get_topic_arns(),
            opts=pulumi.ResourceOptions(parent=lambda_function)
        )

        ##################################
        # Permissions
        ##################################
        lmbda.add_sqs_event_mapping(
            name,
            que.get_que(),
            lambda_function.arn,
            opts=pulumi.ResourceOptions(parent=sns.get_sns_topic())
        )

        self.register_outputs({
            'consumer lamda': lambda_function.arn
        })
