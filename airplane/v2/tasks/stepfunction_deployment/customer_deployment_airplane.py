import time

import airplane

from consts.aws_resources import AwsResources
from consts.aws_account_id import AccountName
from consts.aws_roles import AirplaneEcsEnvVar, AirplaneTaskRole, AwsRole
from pyshared.aws_creds import get_credentialed_client, get_credentialed_resource
from v2.task_models.airplane_task import AirplaneTask
from v2.tasks.stepfunction_deployment import get_sfn_execution_payload

AWS_MAX_NUM_RECEIVE_MSGS = 10


class AwsHandles:

    def __init__(self, account_name: str):
        credentialed_client_kwargs = {
            "arns": AirplaneTaskRole(account_name).CUSTOMER_DEPLOYMENT,
            "desc": "customer_deployment",
            "region": "us-west-2"
        }
        aws_resources = AwsResources(account_name)
        self.cert_arn = aws_resources.CERT_LAMBDA_ARN
        self.cert_role_arn = AwsRole(account_name).CERT_LAMBDA_ROLE
        self.ddb_name = aws_resources.DEPLOYMENT_METADATA_TABLE
        self.ddb_resource = get_credentialed_resource(service_name="dynamodb", **credentialed_client_kwargs)
        self.deployment_queue = get_credentialed_resource(
            service_name="sqs",
            **credentialed_client_kwargs).get_queue_by_name(QueueName=aws_resources.DEPLOYMENT_QUEUE)
        self.sfn_client = get_credentialed_client(service_name="stepfunctions", **credentialed_client_kwargs)
        self.sfn_arn = aws_resources.DEPLOYMENT_STEP_FUNCTION_ARN


class CustomerDeployment(AirplaneTask):

    @staticmethod
    def get_active_deployments_from_sfn(sfn_client, sfn_arn: str):
        paginator = sfn_client.get_paginator('list_executions')
        page_iterator = paginator.paginate(stateMachineArn=sfn_arn, statusFilter="RUNNING")
        return set(execution["name"] for page in page_iterator for execution in page["executions"])

    def get_customers_to_deploy_from_queue(self, active_deployments: set, num_concurrent_deployments: int, queue):
        customers_to_deploy = []
        remaining_deployments = num_concurrent_deployments - len(active_deployments)
        while remaining_deployments > 0:
            msgs = queue.receive_messages(MaxNumberOfMessages=min(remaining_deployments, AWS_MAX_NUM_RECEIVE_MSGS))
            if not msgs:
                break
            additional_customers_to_deploy = self._process_queue_msgs(msgs, active_deployments=active_deployments)
            remaining_deployments -= len(additional_customers_to_deploy)
            customers_to_deploy += additional_customers_to_deploy
        return customers_to_deploy

    @staticmethod
    def _process_queue_msgs(msgs, active_deployments):
        fairytale_name_msg_mapping = {msg.body: msg for msg in msgs}
        additional_customers_to_deploy = set(fairytale_name_msg_mapping.keys()) - active_deployments
        for fairytale_name in additional_customers_to_deploy:
            fairytale_name_msg_mapping[fairytale_name].delete()
        return additional_customers_to_deploy

    @staticmethod
    def get_customer_cfgs_from_ddb(ddb, ddb_name, customers_to_deploy: list[str]):
        all_deployment_cfgs = ddb.meta.client.batch_get_item(RequestItems={
            ddb_name: {
                "Keys": [{
                    "CustomerId": fairytale_name
                } for fairytale_name in customers_to_deploy]
            }
        })
        return {cfg["CustomerId"]: cfg for cfg in all_deployment_cfgs["Responses"][ddb_name]}

    @staticmethod
    def start_sfn_executions(customers_to_deploy: list[str], fairytale_cfgs: dict[str, dict], sfn_client, sfn_arn: str,
                             cert_arn: str, cert_role: str):
        for fairytale_name in customers_to_deploy:
            sfn_client.start_execution(
                stateMachineArn=sfn_arn,
                name=f"{fairytale_name}-deployment-v2-{int(time.time())}",
                input=get_sfn_execution_payload(cfg=fairytale_cfgs[fairytale_name],
                                                cert_lambda_arn=cert_arn,
                                                cert_lambda_role=cert_role),
            )

    @staticmethod
    def get_aws_handles(include_hosted_root: bool, include_panther_root: bool, require_only_one: bool = False):
        handles = []
        if not include_hosted_root and not include_panther_root:
            raise ValueError("Must deploy to one or both or hosted-root and panther-root")
        if require_only_one and include_hosted_root and include_panther_root:
            raise ValueError("Must specify only one org when specifying specific customers to deploy")
        # Deploy to panther-root first if applicable
        if include_panther_root:
            handles.append(AwsHandles(account_name=AccountName.PANTHER_ROOT))
        if include_hosted_root:
            handles.append(AwsHandles(account_name=AccountName.HOSTED_ROOT))
        return handles

    def run(self,
            num_concurrent_deployments: int = 20,
            include_hosted_root: bool = True,
            include_panther_root: bool = True,
            deploy_now_customers: str = ""):
        """Run a batch of deployments in the deployment queue for multiple environments.

        Args:
            num_concurrent_deployments: Number of deployents that can run at the same time, including any that may
                                        already be currently running.
            include_hosted_root: Deploy customers in the hosted-root org
            include_panther_root: Deploy staging customers
            deploy_now_customers: A comma separate list of customers that should preempt the priority queue. If given,
                                  they must all within one org, and the org they are not in (the include arg) should be
                                  set to false. This will only deploy those customers and will ignore any others in the
                                  deployment queue.
        """
        customers_to_deploy = [customer.strip() for customer in deploy_now_customers.split(",") if customer]
        only_deploy = bool(customers_to_deploy)
        for aws in self.get_aws_handles(include_hosted_root, include_panther_root, require_only_one=only_deploy):
            if not only_deploy:
                active_deployments = self.get_active_deployments_from_sfn(aws.sfn_client, aws.sfn_arn)
                customers_to_deploy += self.get_customers_to_deploy_from_queue(active_deployments,
                                                                               num_concurrent_deployments,
                                                                               aws.deployment_queue)
            customer_cfgs = self.get_customer_cfgs_from_ddb(aws.ddb_resource, aws.ddb_name, customers_to_deploy)
            self.start_sfn_executions(customers_to_deploy, customer_cfgs, aws.sfn_client, aws.sfn_arn, aws.cert_arn,
                                      aws.cert_role_arn)
        return {"customers_deployed": customers_to_deploy}


task = airplane.task(name=f"Customer Deployment",
                     slug="customer_deployment_tscott_test",
                     env_vars=[AirplaneEcsEnvVar().CUSTOMER_DEPLOYMENT])(CustomerDeployment().run)
