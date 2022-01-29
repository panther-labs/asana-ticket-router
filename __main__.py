# Copyright (C) 2020 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.

import os
import shutil
import subprocess  # nosec: True

import pulumi

from sentry_asana_integration.pulumi.sentry_asana_integration import \
    SentryAsanaIntegration

LAMBDA_DEPLOYMENT_PACKAGE_DIR = '.lambda-deployment'


def create_lambda_deployment_packages() -> None:
    """A helper function for creating the lambda deployment packages."""
    shutil.rmtree(LAMBDA_DEPLOYMENT_PACKAGE_DIR, ignore_errors=True)
    os.mkdir(LAMBDA_DEPLOYMENT_PACKAGE_DIR)

    # sentry_asana_integration deployment package
    os.mkdir(f'{LAMBDA_DEPLOYMENT_PACKAGE_DIR}/sentry_asana_integration')
    # copy all src files into new dir; shutil.copytree, the most suggested way of doing this
    # in python, apparently has some issues that cause unexpected headaches
    subprocess.call(  # nosec: True
        ['cp', '-r', 'sentry_asana_integration/src',
            f'{LAMBDA_DEPLOYMENT_PACKAGE_DIR}/sentry_asana_integration'],
        shell=False
    )
    subprocess.call(  # nosec: True
        [
            'pip',
            'install',
            '-r',
            'sentry_asana_integration/requirements.txt',
            '-t',
            f'{LAMBDA_DEPLOYMENT_PACKAGE_DIR}/sentry_asana_integration'
        ],
        shell=False
    )


pulumi.log.info('Attempting to create the Lambda deployment packages')
create_lambda_deployment_packages()
sentry_asana_integration = SentryAsanaIntegration(
    'sentry-asana',
    f'./{LAMBDA_DEPLOYMENT_PACKAGE_DIR}/sentry_asana_integration'
)

pulumi.export('sentry-asana-apigw-endpoint',
              sentry_asana_integration.apigw_endpoint)
