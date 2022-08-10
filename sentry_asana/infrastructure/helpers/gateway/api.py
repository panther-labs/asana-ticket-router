# Copyright (C) 2022 Panther Labs Inc
#
# Panther Enterprise is licensed under the terms of a commercial license available from
# Panther Labs Inc ("Panther Commercial License") by contacting contact@runpanther.com.
# All use, distribution, and/or modification of this software, whether commercial or non-commercial,
# falls under the Panther Commercial License to the extent it is permitted.
import pulumi_aws as aws
import pulumi


def create(
    name: str, lambda_arn: str, opts: pulumi.ResourceOptions
) -> aws.apigatewayv2.Api:
    """Create an API Gateway endpoint"""
    return aws.apigatewayv2.Api(
        resource_name=f'{name}-api',
        protocol_type='HTTP',
        route_key='POST /',
        target=lambda_arn,
        opts=opts,
    )
