"""
Lambda function to set trial shutdown flag for customer in hosted-deployments repo
"""
import tempfile
import json

from os_util import join_paths, get_current_dir, change_dir, load_py_file_as_module
from git_util import HostedDeploymentsGitRepo
from yaml_util import upsert_file_value, get_file_value


def generate_deployment_target(repo: HostedDeploymentsGitRepo) -> None:
    pwd = get_current_dir()
    change_dir(repo.path)
    module = load_py_file_as_module(
        filepath="./automation-scripts/generate.py")
    module.generate_configs()
    change_dir(pwd)


def get_customer_path(repo: HostedDeploymentsGitRepo, customer_id: str) -> str:
    return join_paths(repo.path, "deployment-metadata", "deployment-targets", f"{customer_id}.yml")


def get_customer_generated_path(repo: HostedDeploymentsGitRepo, customer_id: str) -> str:
    return join_paths(repo.path, "deployment-metadata", "generated", f"{customer_id}.yml")


def set_shutdown_param(repo: HostedDeploymentsGitRepo, customer_id: str, reason: str) -> None:
    customer_path = get_customer_path(repo, customer_id)
    upsert_file_value(
        customer_path, "CloudFormationParameters.TrialShutdown", reason)


def is_trial_customer(repo: HostedDeploymentsGitRepo, customer_id: str) -> bool:
    customer_path = get_customer_path(repo, customer_id)
    sales_phase = get_file_value(
        customer_path, "CloudFormationParameters.SalesPhase")
    if sales_phase == "trial":
        return True
    return False


def get_hd_repo() -> HostedDeploymentsGitRepo:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = HostedDeploymentsGitRepo(tmp_dir, "master")
        return repo


def lambda_handler(event, _):
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    customer_id = sns_message.get("customer_id", False)
    reason = sns_message.get("reason", False)
    notes = sns_message.get("notes", "<no notes provided by instance>")

    if customer_id:
        print(f"Trial account suspension requested for customer {customer_id}")
    else:
        print(f"No customer_id field passed in SNS event")
        exit(1)

    if reason in ["cost", "time"]:
        print(f"Suspension reason is {reason}")
    else:
        print(f"No reason field passed in SNS event.  Valid values are 'cost' and 'time'")
        exit(1)

    hd_repo = get_hd_repo()
    if is_trial_customer(hd_repo, customer_id):
        print(
            f"Customer {customer_id} is confirmed to be a trial account according to hosted-deployments repository")
    else:
        print(
            f"Customer {customer_id} does not appear to be a trial account according to hosted-deployments repository")
        print("Cowardly refusing to modify this customer")
        exit(1)

    print("Modifying customer entry in hosted-deployments repo and committing to master")
    set_shutdown_param(hd_repo, customer_id, reason)
    generate_deployment_target(hd_repo)
    hd_repo.add_commit_and_push(
        f"Automated shutdown of trial instance: {customer_id}",
        description=f"This action was performed by the automated lambda/SNS queue in hosted-ops.\n\nReason: {reason}\nAdditional Notes: {notes}",
        filepaths=[
            get_customer_path(hd_repo, customer_id),
            get_customer_generated_path(hd_repo, customer_id)
        ]
    )
    print("Git push complete")
    return event
