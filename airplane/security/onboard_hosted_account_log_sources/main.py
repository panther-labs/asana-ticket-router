# Linked to https://app.airplane.dev/t/onboard_hosted_account_log_sources [do not edit this line]
"""
A script to automate the creation of both S3 and Cloud Account sources in
panther-hosted-security. This script can be used to onboard new AWS accounts to
an existing panther instance or migrate sources to a new panther instance.

"""

import argparse
import boto3
import json
import os
import re

# payload for creating a S3 source integration
def create_s3_input(account_id, s3_bucket, log_processing_arn, kms_key):
    payload_s3 = {
        "putIntegration": {
            "integrationLabel": "s3-hosted-" + account_id,
            "integrationType": "aws-s3",
            "userId":"1",
            "aWSAccountID": account_id,
            "cWEEnabled": False,
            "enabled": True,
            "s3Bucket": s3_bucket,
            "kmsKey": kms_key,
            "s3PrefixLogTypes": [{
                "s3Prefix": "",
                "logTypes": ["AWS.ALB", "AWS.S3ServerAccess", "AWS.VPCFlow"]
            }],
            "managedBucketNotifications": True,
            "logProcessingRole": log_processing_arn
        }
    }

    return payload_s3


# payload for creating a cloud account integration
def create_cloud_account_payload(account_id):
    payload_cloud_account = {
        "putIntegration": {
            "integrationLabel": "cloud-hosted-" + account_id,
            "integrationType": "aws-scan",
            "userId": "1",
            "aWSAccountID": account_id,
            "cWEEnabled": False,
            "scanIntervalMins": 1440
        }
    }

    return payload_cloud_account


# call the lambda function panther-source-api:putIntegration
def create_log_integration(payload, lambda_client):
    response = lambda_client.invoke(FunctionName="panther-source-api",
                                    InvocationType="RequestResponse",
                                    Payload=bytes(json.dumps(payload),
                                                  'utf-8'))

    response_payload = json.loads(response['Payload'].read())

    if (response.get("ResponseMetadata").get("HTTPStatusCode") != 200
            or response.get("FunctionError") == "Unhandled"):
        print("[+] Something went wrong.")
        print("[+] Response headers:")
        print(response)
        print("[+] Response payload:")
        print(response_payload)
    else:
        print("[+] Success. Health status:")

        for k, v in response_payload.get("health").items():
            print("\t" + k + ":\t\t" + str(v))


def check_s3_notifications(s3_bucket, s3_client):
    """
    Checks for existing S3 bucket notifications.

    Panther uses S3 bucket notifications to know when to pull new data from an
    S3 bucket. These are enabled by default. If a bucket already has S3 notifcations
    configured than the source onboarding will fail. This method checks for
    existing notifications and clears them if they are found so that Panther
    can add them during the source setup.
    """

    response = s3_client.get_bucket_notification_configuration(
        Bucket=s3_bucket)

    if response.get("TopicConfigurations") is None:
        print("[+] No existing bucket notifications found.")
        return True

    if ("panther-managed-" in response.get("TopicConfigurations")[0].get("Id")
            or "panther-auditlog-"
            in response.get("TopicConfigurations")[0].get("TopicArn")
            or "panther-notifications-"
            in response.get("TopicConfigurations")[0].get("TopicArn")):

        print(
            "[+] Existing panther-managed bucket notifications found. Attempting to remove."
        )

        # notifications are enabled, to delete them we need to apply a blank config
        response = s3_client.put_bucket_notification_configuration(
            Bucket=s3_bucket, NotificationConfiguration={})

        if response.get("ResponseMetadata").get("HTTPStatusCode") == 200:
            print("[+] Success. " +
                  str(response.get("ResponseMetadata").get("HTTPStatusCode")))
            return True
        else:
            print("[+] Removing notifications unsuccessful.")
            return False
    else:
        print(
            "[+] An unknown (non-Panther) notification topic was configured. Please review."
        )
        print(response)


def find_audit_log_s3(s3_client):
    """ Determines the unique name of the panther auditlogs S3 bucket for a given account """

    response = s3_client.list_buckets()
    for bucket in response.get("Buckets"):
        if (re.match("panther-bootstrap.*-auditlogs-.*", bucket.get("Name"))
                or re.match("panther-panther-.*-auditlogs-.*",
                            bucket.get("Name"))
                or re.match("panther-master-.*-auditlogs-.*",
                            bucket.get("Name"))):

            return bucket.get("Name")


def get_client(service, role):
    sess = boto3.Session()
    sts_client = sess.client("sts")

    sts_creds = get_credentials(sts_client, role)

    assumed_client = sess.client(
        service,
        aws_access_key_id=sts_creds['AccessKeyId'],
        aws_secret_access_key=sts_creds['SecretAccessKey'],
        aws_session_token=sts_creds['SessionToken'],
        region_name="us-east-2",
    )

    return assumed_client


def get_credentials(sts_client, role):
    assumed_role_object = sts_client.assume_role(
        RoleArn=role, RoleSessionName="log-onboarding-session")

    credentials = assumed_role_object['Credentials']

    return credentials


def cli():
    parser = argparse.ArgumentParser(
        description='Onboard hosted account S3 and cloud sources into panther-hosted-security')
    parser.add_argument("--account_id", "-a",
        help="The AWS account ID of the hosted account you are onboarding.", required=True)
    parser.add_argument("--s3_bucket", "-s3",
        help="The S3 bucket holding the Panther audit logs for this account", required=False)
    parser.add_argument("--aws_s3",
        help="Add an S3 log source to monitor the instance.", required=False, action='store_true')
    parser.add_argument("--aws_scan",
        help="Add a cloud account to monitor.", required=False, action='store_true')
    parser.add_argument("--log_processing_arn", "-lp_arn",
        help="The ARN of the log processing role", required=False)
    parser.add_argument("--s3_onboarding_role_arn", "-s3_arn",
        help="The arn of the role that can be assumed in the customer's hosted account.",
        required=False )
    parser.add_argument("--source_onboarding_role_arn", "-source_arn",
        help="The arn of the role that can be assumed in hosted-security to invoke panther-source-api.",
        required=False )
    parser.add_argument("--kms_key", "-kms",
        help="The KMS key used by the S3 bucket.",
        required=False )


    args = parser.parse_args()
    run(args)

def run(args):

    # if neither option is specified run both
    if not (args.aws_s3 or args.aws_scan):
        args.aws_s3 = True
        args.aws_scan = True

    # if the HostedSourceOnboardingRole is not specified use the default
    if not args.s3_onboarding_role_arn:
        args.s3_onboarding_role_arn = "arn:aws:iam::" + args.account_id + ":role/HostedSourceOnboardingRole"

    # if the SecuritySourceOnboardingRole is not specified use the default in hosted-security
    if not args.source_onboarding_role_arn:
        args.source_onboarding_role_arn = "arn:aws:iam::964675078129:role/SecuritySourceOnboardingRole"

    # if no KMS key is provided do not use one.
    if not args.kms_key:
        args.kms_key = ""

    # Create the boto3 clients using the assumed role credentials.
    # Apparently using boto3 resources would be easier, I didn't realize these were a thing.
    s3_client = get_client("s3", args.s3_onboarding_role_arn)
    lambda_client = get_client("lambda", args.source_onboarding_role_arn)

    if args.aws_s3:
        # if no ARN specified, assume we will use the default LogProcessingRole
        if not args.log_processing_arn:
            args.log_processing_arn = ("arn:aws:iam::" + args.account_id +
                                ":role/PantherLogProcessingRole-" + args.account_id)
            print("[+] LogProcessingRole not provided, using " + args.log_processing_arn)

        # find the bucket name if not provided
        if not args.s3_bucket:
            print("[+] S3 bucket not provided, searching for the audit logs S3 bucket in account: " + args.account_id)
            args.s3_bucket = find_audit_log_s3(s3_client)
            if args.s3_bucket:
                print("[+] Found S3 bucket: " + args.s3_bucket)
            else:
                print("[+] Auditlogs S3 not found, exiting.")
                raise RuntimeError("Auditlogs S3 not found")


        print("[+] Checking for existing S3 notifications.")
        if check_s3_notifications(args.s3_bucket, s3_client):
            print("[+] Building the putIntegration payload.")
            payload_s3 = create_s3_input(args.account_id, args.s3_bucket, args.log_processing_arn, args.kms_key)

            print("[+] Attempting to create the new log source.")
            create_log_integration(payload_s3, lambda_client)

    if args.aws_scan:
        # add the cloud account integration
        print("[+] Adding cloud account for scanning.")
        payload_cloud_account = create_cloud_account_payload(args.account_id)
        create_log_integration(payload_cloud_account, lambda_client)


def main(params):
    if not os.getenv("AIRPLANE_SESSION_ID"):
        raise RuntimeError("This task must be run from within a runbook!")

    aws_account_id = params["aws_account_id"]

    args = Namespace(
        account_id = aws_account_id,
        s3_bucket = "",
        aws_s3 = True,
        aws_scan = True,
        log_processing_arn = "",
        s3_onboarding_role_arn = "",
        source_onboarding_role_arn = "",
        kms_key = ""
    )
    
    run(args)


class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


if __name__ == "__main__":
    cli()
