import os
import shutil
import sys

import boto3

from pyshared.aws_creds import get_credentialed_client
from pyshared.git_ops import git_clone, git_add_commit_push
from pyshared.os_utils import tmp_change_dir
from pyshared.yaml_utils import load_yaml_cfg, save_yaml_cfg

REPOSITORY = "conduit-deployments"
GREYNOISE_PARAM_FILE = "greynoise_prod.yml"
LOCAL_PARAM_FILE = "test_cfn_params.yml"  # Used for testing/dry runs
LOCAL_PARAM_TMPL = "test_cfn_params.yml.tmpl"  # ditto

# todo:
# parameterize for Conduit staging runs
# add handling for removing access
# add handling for IpInfo (likely a separate script)
# add handling for CPaaS/self-hosted customers (maybe not worth doing)
# refactor to use library dry run resources


def fetch_lambda_role_arn(aws_account_id: str, region: str) -> str:
    """Fetch the ARN of the role used by the target customer's
    Lookup API Lambda function

    Args:
        aws_account_id: The ID of the customer's AWS account
        region: the region where their Panther instance is running

    Returns:
        The ARN as a string
    """
    client = boto3.client('lambda')
    role = f"arn:aws:iam::{aws_account_id}:role/AirplaneConduitReadOnly"
    client = get_credentialed_client(service_name="lambda", arns=[role], region=region, desc="airplane")
    lookup_lambda = client.get_function(FunctionName="panther-lookup-tables-api")
    return lookup_lambda["Configuration"]["Role"]


def update_yaml_file(file_path, arn) -> None:
    """Update the specified Cfn parameter YAML file by adding the customer's
    role ARN to the list of full access GreyNoise ARNs

    Args:
        file_path: The path to the target YAML file
        arn: the ARN of the customer's role
    """
    cfn_yaml = load_yaml_cfg(file_path, error_msg=f"GreyNoise parameter file not found: '{file_path}'")
    current_arns = cfn_yaml["CloudFormationParameters"]["GreyNoiseFullAccessARNs"]
    print(f"Granting full GreyNoise access to the following role arn {arn}")
    if arn in current_arns:
        print("ERROR: The role ARN has already been granted full GreyNoise access!")
        sys.exit(1)
    cfn_yaml["CloudFormationParameters"]["GreyNoiseFullAccessARNs"].append(arn)
    save_yaml_cfg(cfg_filepath=file_path, cfg=cfn_yaml)


def main(params: dict) -> dict:
    aws_account_id, region = params["aws_account_id"], params["region"]
    role_arn = fetch_lambda_role_arn(aws_account_id, region)
    dry_run_mode = params["dry_run"]

    if not dry_run_mode:
        repository_dir = git_clone(repo=REPOSITORY, github_setup=True, existing_dir=None)
        param_file_abs_path = os.path.join(repository_dir, GREYNOISE_PARAM_FILE)
        update_yaml_file(param_file_abs_path, role_arn)
        with tmp_change_dir(change_dir=repository_dir):
            commit_title = f'Granting {params["fairytale_name"]} access to paid GreyNoise resources'
            git_add_commit_push(files=[GREYNOISE_PARAM_FILE], title=commit_title, description='')
    else:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        cfn_yaml_file = cfg_filepath = os.path.join(script_dir, LOCAL_PARAM_FILE)
        cfn_yaml_tmpl = cfg_filepath = os.path.join(script_dir, LOCAL_PARAM_TMPL)
        # reset LOCAL_PARAM_FILE from LOCAL_PARAM_TMPL so that no one accidentally commits it to this repo
        if os.path.exists(LOCAL_PARAM_FILE):
            os.remove(LOCAL_PARAM_FILE)
        shutil.copy(cfn_yaml_tmpl, cfn_yaml_file)
        print(f"Processing the local test file {cfn_yaml_file}")
        update_yaml_file(cfn_yaml_file, role_arn)


if __name__ == "__main__":
    # This input blob is for a customer dev account, which importantly lives under the hosted root account
    # All Panther deployments under the identity root automatically get full GreyNoise access i.e. they are
    # not valid test environments for this Airplane task
    test_params = {
        "fairytale_name": "yog-sothoth",
        "aws_account_id": "135118505289",
        "region": "us-west-2",
        "dry_run": True
    }
    main(test_params)
