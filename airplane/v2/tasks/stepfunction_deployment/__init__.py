import decimal
import json


class DecimalEncoder(json.JSONEncoder):

    def default(self, o):
        """Decimal to int"""
        if isinstance(o, decimal.Decimal):
            return int(o)
        return super().default(o)


def get_sfn_execution_payload(cfg, cert_lambda_arn, cert_lambda_role):
    payload = {
        "version": "v2",
        "development": cfg.get("Development", False),
        "panther_cf_template_url": cfg["PantherTemplateURL"],
        "required_stacksets": cfg["GithubConfiguration"].get("RequiredStacksets", []),
        "customer_id": cfg["CustomerId"],
        "customer_region": cfg["GithubConfiguration"]["CustomerRegion"],
        "base_root_email": cfg["GithubConfiguration"]["BaseRootEmail"],
        "customer_role_name": cfg.get("CustomerRoleName", "PantherDeploymentRole"),
        "cert_lambda_arn": cert_lambda_arn,
        "cert_lambda_role": cert_lambda_role,
        "panther_stack_name": cfg.get("PantherStackName", "panther"),
        "aws_configuration": cfg["AWSConfiguration"],
        "config_parameters": cfg["GithubCloudFormationParameters"],

        # Used by create_panther_cert
        "cert_parameters": cfg.get("CertParameters", {}),

        # For compatibility / sfn
        "deployment_metadata": {
            "CloudFormationParameters": {},
            "DeploymentType": cfg.get("DeploymentType", ""),
            "LegacyDeployment": cfg.get("LegacyDeployment", False)
        },
        "snowflake": cfg.get("Snowflake", {"Type": "none"}),
        "outputs": {},
    }

    # These settings are only required for SaaS
    # HostedZone / OrgRootId / InitialOUId / TargetOUId
    if "HostedZone" in cfg["GithubConfiguration"]:
        payload["hosted_zone"] = {
            "name": cfg["GithubConfiguration"]["HostedZone"]["Name"],
            "id": cfg["GithubConfiguration"]["HostedZone"]["Id"],
        }

    aws_configuration = cfg["AWSConfiguration"]
    if "OrgRootId" in aws_configuration:
        payload["org_root_id"] = aws_configuration["OrgRootId"]
    if "InitialOUId" in aws_configuration:
        payload["initial_ou_id"] = aws_configuration["InitialOUId"]
    if "TargetOUId" in aws_configuration:
        payload["target_ou_id"] = aws_configuration["TargetOUId"]

    # Required by sfn template
    # $.deployment_metadata.AccountId
    if "AccountId" in cfg["AWSConfiguration"] and cfg["AWSConfiguration"]["AccountId"] != "":
        payload["deployment_metadata"]["AccountId"] = cfg["AWSConfiguration"]["AccountId"]

    # $.deployment_metadata.CloudFormationParameters.SnowflakeDestinationClusterARNs
    if "SnowflakeDestinationClusterARN" in cfg.get("Snowflake", {}):
        payload["deployment_metadata"]["CloudFormationParameters"].update({
            "SnowflakeDestinationClusterARNs":
            cfg["Snowflake"]["SnowflakeDestinationClusterARN"],
        })
    if "SnowflakeDestinationClusterARNs" in cfg["GithubCloudFormationParameters"]:
        payload["deployment_metadata"]["CloudFormationParameters"].update({
            "SnowflakeDestinationClusterARNs":
            cfg["GithubCloudFormationParameters"]["SnowflakeDestinationClusterARNs"],
        })

    return json.dumps(payload, cls=DecimalEncoder)
