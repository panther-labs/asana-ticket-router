# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
from typing import List

import json
import pulumi_aws as aws
import pulumi


def create(name: str, inline_policies: List[aws.iam.RoleInlinePolicyArgs], opts: pulumi.ResourceOptions) -> aws.iam.Role:
    """Create a new IAM Role"""
    name = f'{name}-role'
    return aws.iam.Role(
        resource_name=name,
        name=name,
        description=f'IAM Role for {name} to assume',
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
        opts=opts,
    )
