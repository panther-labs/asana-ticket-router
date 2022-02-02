# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import pulumi

from sentry_asana.infrastructure.producer import Producer
from sentry_asana.infrastructure.consumer import Consumer
from sentry_asana.infrastructure.queue import Queue
from sentry_asana.infrastructure.sns import Sns
from sentry_asana.infrastructure.globals import IS_DEBUG,\
    PROJECT_NAME, LAMBDA_CONSUMER, LAMBDA_PRODUCER

##################################
# MAIN
##################################
pulumi.log.info('Creating Topics')
sns = Sns(
    name=f'{PROJECT_NAME}'
)


pulumi.log.info('Creating Queues')
que = Queue(
    name=f'{PROJECT_NAME}-message',
    sns=sns
)


pulumi.log.info('Creating Producer')
producer = Producer(
    name=f'{PROJECT_NAME}-{LAMBDA_PRODUCER}',
    que=que,
    sns=sns,
    is_debug=IS_DEBUG,
    opts=pulumi.ResourceOptions(
        depends_on=[que]
    )
)

pulumi.log.info('Creating Consumer')
consumer = Consumer(
    name=f'{PROJECT_NAME}-{LAMBDA_CONSUMER}',
    que=que,
    sns=sns,
    is_debug=IS_DEBUG,
    opts=pulumi.ResourceOptions(
        depends_on=[que]
    )
)

pulumi.export(
    f'sentry-asana-apigw-endpoint-{LAMBDA_PRODUCER}', producer.apigw_endpoint)
