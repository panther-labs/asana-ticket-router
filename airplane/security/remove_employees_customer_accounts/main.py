import boto3
import re

from argparse import ArgumentParser

EMAIL_PATTERN = "(run)?panther.(io|com){1}"  #also covers any @runpanther.io legacy accts or new panther.com accounts


def get_client(service:str, role:str, region:str):
    sess = boto3.Session()
    sts_client = sess.client("sts")

    sts_creds = get_credentials(sts_client, role)

    assumed_client = sess.client(
        service,
        aws_access_key_id=sts_creds['AccessKeyId'],
        aws_secret_access_key=sts_creds['SecretAccessKey'],
        aws_session_token=sts_creds['SessionToken'],
        region_name=region,
    )

    return assumed_client    


def get_credentials(sts_client, role):
    assumed_role_object = sts_client.assume_role(
        RoleArn=role, RoleSessionName="panther-employee-acct-removal")

    credentials = assumed_role_object['Credentials']

    return credentials


def get_panther_pool_id(user_pools) -> str:
    for pool in user_pools:
        if pool.get('Name') == 'panther-users':
            return pool.get('Id')


def get_panther_users(users, user_email) -> dict:
    count = 0
    panther_employees = {}

    for user in users:
        for attr in user.get('Attributes'):
            if attr.get('Name') == 'email':
                # only allow removal of panther employee addresses
                if re.search(EMAIL_PATTERN, attr.get('Value')) is not None:
                    # only remove the employee whose email was added in the form
                    if attr.get('Value').lower() == user_email.lower():
                        print(f"[*] Found Panther Employee: {attr.get('Value')}")
                        panther_employees[user.get('Username')] = attr.get('Value')
                        count += 1
    
    if count == 0:
        print("[-] No Panther employees found.")

    return panther_employees


def run(params):
    role = 'arn:aws:iam::' + params.account_id + ':role/AirplaneUserRemovalRole'

    cognito_client = get_client('cognito-idp', role, params.region)

    try:
        response = cognito_client.list_user_pools(MaxResults = 10)
    except boto3.ClientError as e:
        print(e)
        raise RuntimeError("Panther Congnito User Pool could not be found")

    panther_pool_id = get_panther_pool_id(response.get('UserPools'))
    
    try:
        response = cognito_client.list_users(UserPoolId = panther_pool_id)
    except boto3.ClientError as e:
        print(e)
        raise RuntimeError("Users could not be listed from the Panther User Pool")

    remove_dict = get_panther_users(response.get('Users'), params.email)

    if remove_dict == {}:
        print("[-] No users to remove. Exiting.")
        return 0

    if params.dry_run:
        print("[*] Dry run, no action taken, the accounts above would be removed in a normal run.")
        return 0
    for username,email in remove_dict.items():
        try:
            response = cognito_client.admin_delete_user(UserPoolId=panther_pool_id,Username=username)
            print(f"[+]   User with email address {email} and userID {username} was removed.")
        except boto3.ClientError as e:
            print(e)
            raise RuntimeError("Account was not removed")
                

def main(params):
    aws_account_id = params["account_id"]
    aws_region = params["region"]
    user_email = params["user_email"]
    dry_run_param = params["dry_run"]

    args = Namespace(
        account_id = aws_account_id,
        region = aws_region,
        email = user_email,
        dry_run = dry_run_param
    )

    run(args)


class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


if __name__ == '__main__':

    parser = ArgumentParser(
        description='Remove Panther Employee accounts from a Panther instance.')
    parser.add_argument("--account_id", "-a",
         help="The AWS account ID of the hosted account you are removing users from.", required=True)
    parser.add_argument("--region", "-r",
         help="The AWS account region of the hosted account you are removing users from.", required=True)
    parser.add_argument("--dry_run", "-d",
         help="During a dry run the tool will print users to remove but not perform the actual removal.", required=False, action='store_true')

    args = parser.parse_args()
    if not args.dry_run:
        args.dry_run = False

    run(args)
