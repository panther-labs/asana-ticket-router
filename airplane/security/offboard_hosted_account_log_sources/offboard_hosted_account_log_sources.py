"""
A script to automate the deletion of both S3 and Cloud Account sources in
panther-hosted-security. This script can be used to offboard AWS accounts from
an existing panther instance.

"""

import argparse
import boto3
import json
from typing import Optional
from pyshared.aws_creds import get_credentialed_client


# Namespace copy-pasta'ed for main from onboard_hosted_account_log_sources
class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


# payload for listing log source integrations
def list_srcintegration_input(account_id:str):
    payload = {
        "listSourceIntegrations" : {
            "integrationTypes": [
                "aws-scan",
                "aws-s3",
            ],
            "includeHealthCheck": False,
            "nameIncludes": account_id,
            "pageSize": 25
        }
    }
    return payload


def delete_integration_input(integrationId:str):
    payload = {
        "deleteIntegration" : {
            "integrationId": integrationId
            }
    }
    return payload


def offboard_log_integration(lambda_client, aws_account_id:str):
    list_req_body = list_srcintegration_input(aws_account_id)
    list_request = lambda_client.invoke(
        FunctionName="panther-source-api",
        InvocationType="RequestResponse",
        Payload=bytes(json.dumps(list_req_body), 'utf-8'),
    )
    list_response = json.loads(list_request.get('Payload').read())
    if (list_request.get("ResponseMetadata", {}).get("HTTPStatusCode", 0) != 200
            or list_request.get("FunctionError") == "Unhandled"):
        print("[+] Something went wrong listing integrations.")
        print("[+] Request body:")
        print(list_req_body)
        print("[+] Response payload:")
        print(list_response)
        raise RuntimeError("Errors returned when listing out integrations. Cannot continue.")
    else:
        print("[+] Success listing integrations.")
 
    integrations_to_delete = []
    for integration in list_response.get("integrations", []):
        if integration.get("awsAccountId", "") != aws_account_id:
            continue
        print(f"[+] Queueing integrationId {integration.get('integrationId')} - {integration.get('integrationLabel')} - {integration.get('integrationType')} for deletion")
        integrations_to_delete.append(integration.get("integrationId"))
    
    if not integrations_to_delete:
        print(f"[+] No integrations with account id {aws_account_id}")
        # return will lead to airplane reporting success, which is ok in this scenario
        return
    
    for integration in integrations_to_delete:
        # Do delete here
        del_req_body = delete_integration_input(integrationId=integration)
        del_request = lambda_client.invoke(
            FunctionName="panther-source-api",
            InvocationType="RequestResponse",
            Payload=bytes(json.dumps(del_req_body), 'utf-8'),
        )
        del_response = json.loads(del_request.get('Payload').read())
        if (del_request.get("ResponseMetadata", {}).get("HTTPStatusCode", 0) != 200
                or del_request.get("FunctionError") == "Unhandled"):
            print(f"[+] Something went wrong deleting integration {integration}.")
            print("[+] Request body:")
            print(del_req_body)
            print("[+] Response payload:")
            print(del_response)
            # We move onto the next item in our to be deleted list
            continue
        else:
            print(f"[+] Deleted integrationId {integration}")


def get_client(session:Optional[boto3.session.Session], role:str, boto3_client_name:str):
    if session is None:
        # Create a default identity based session
        session = boto3.Session()
    sts_client = session.client('sts')
    assumed_role_creds = sts_client.assume_role(
        RoleArn=role,
        RoleSessionName="log-offboarding-session"
        )
    # Our clients are always in us-east-2 for king-of-spades
    assumed_role_sess =  boto3.session.Session(
        aws_access_key_id=assumed_role_creds['Credentials']['AccessKeyId'],
        aws_secret_access_key=assumed_role_creds['Credentials']['SecretAccessKey'],
        aws_session_token=assumed_role_creds['Credentials']['SessionToken'],
    )
    return assumed_role_sess.client(boto3_client_name, region_name="us-east-2")


def cli():
    parser = argparse.ArgumentParser(
        description='Offboard hosted account S3 and cloud sources from panther-hosted-security')
    parser.add_argument("--account_id", "-a",
        help="The AWS account ID of the hosted account you are onboarding.", required=True)
    parser.add_argument("--source_offboarding_role_arn", "-source_arn",
        help="The arn of the role that can be assumed in hosted-security to invoke panther-source-api.",
        required=False )

    args = parser.parse_args()
    run(args)

def run(args):
    # setup a default session using whatever identity we're invoked with
    sess = boto3.Session()

    # if the SecuritySourceOnboardingRole is not specified use the default in hosted-security
    if not args.source_offboarding_role_arn:
        args.source_offboarding_role_arn = "arn:aws:iam::964675078129:role/SecuritySourceOnboardingRole"

    # lambda client for executing lambda:InvokeFunction
    lambda_client = get_client(sess, args.source_offboarding_role_arn, 'lambda')
    offboard_log_integration(lambda_client=lambda_client, aws_account_id=args.account_id)



def main(params):
    aws_account_id = params["aws_account_id"]
    args = Namespace(
        account_id = aws_account_id
    )
    run(args)


if __name__ == "__main__":
    cli()
