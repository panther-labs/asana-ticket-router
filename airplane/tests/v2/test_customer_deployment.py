import json
from unittest import mock

import boto3
from moto import mock_sqs, mock_stepfunctions, mock_sts
import pytest

from consts.aws_account_id import AccountId
from pyshared.aws_creds import get_credentialed_resource
from tests import change_airplane_env_var
from v2.tasks.stepfunction_deployment.customer_deployment_airplane import CustomerDeployment

CUSTOMER_NAMES = ["hello", "there-1", "lots", "of", "names", "there-2"]
DEPLOYMENT_QUEUE_NAME = "deployment.fifo"


class TestCustomerDeployment:

    @pytest.fixture(autouse=True, scope="function")
    def setup(self):
        with mock_sqs():
            with mock_stepfunctions():
                with mock_sts():
                    with change_airplane_env_var("AIRPLANE_RUNNER_ID", 1):
                        # noinspection PyAttributeOutsideInit
                        self.hosted_root_sqs = get_credentialed_resource(
                            "sqs",
                            arns=f"arn:aws:iam::{AccountId.HOSTED_ROOT}role/CustomerDeployment",
                            desc="test",
                            region="us-west-2")
                        self.panther_root_sqs = get_credentialed_resource(
                            "sqs",
                            arns=f"arn:aws:iam::{AccountId.PANTHER_ROOT}:role/CustomerDeployment",
                            desc="test",
                            region="us-west-2")

                        # noinspection PyAttributeOutsideInit
                        self.sfn = boto3.client("stepfunctions", region_name="us-west-2")
                        # noinspection PyAttributeOutsideInit
                        self.sts = boto3.client("sts")
                        # noinspection PyAttributeOutsideInit
                        self.customer_deployment = CustomerDeployment()
                        yield

    def create_sfn(self):
        definition = json.dumps({
            "StartAt": "DefaultState",
            "States": "",
            "DefaultState": {
                "Type": "Fail",
                "Error": "DefaultStateError",
                "Cause": "No Matches!"
            }
        })
        return self.sfn.create_state_machine(
            name="MyStepFunction",
            definition=definition,
            roleArn=f"arn:aws:iam::123456789012:role/sf_role",
        )["stateMachineArn"]

    @staticmethod
    def setup_queue(queue_resource, add_msgs):
        queue = queue_resource.create_queue(QueueName=DEPLOYMENT_QUEUE_NAME, Attributes={'FifoQueue': 'true'})
        if add_msgs:
            for name in CUSTOMER_NAMES:
                queue.send_message(MessageGroupId="deployment", MessageBody=name)
        return queue

    def mock_customer_deployment_funcs(self, customers_to_deploy):
        self.customer_deployment.get_aws_handles = mock.MagicMock()
        self.customer_deployment.get_aws_handles.return_value = [mock.MagicMock(), mock.MagicMock()]
        self.customer_deployment.get_active_deployments_from_stepfunction = lambda *args, **kwargs: None
        self.customer_deployment.get_customers_to_deploy_from_queue = lambda *args, **kwargs: customers_to_deploy
        self.customer_deployment.start_sfn_executions = lambda *args, **kwargs: None

    def test_get_active_deployments_from_list(self):
        arn = self.create_sfn()
        for name in CUSTOMER_NAMES:
            self.sfn.start_execution(stateMachineArn=arn, name=name)
        assert sorted(self.customer_deployment.get_active_deployments_from_sfn(self.sfn, arn)) == sorted(CUSTOMER_NAMES)

    def test_get_customers_to_deploy_from_queue_concurrency_amount_bigger_than_queue_size(self):
        queue = self.setup_queue(queue_resource=self.hosted_root_sqs, add_msgs=True)
        customers_to_deploy = sorted(
            self.customer_deployment.get_customers_to_deploy_from_queue(active_deployments=set(),
                                                                        num_concurrent_deployments=10,
                                                                        queue=queue))
        assert customers_to_deploy == sorted(CUSTOMER_NAMES)
        assert int(queue.attributes["ApproximateNumberOfMessages"]) == 0

    def test_get_customers_to_deploy_from_queue_active_customers(self):
        total_in_queue = len(CUSTOMER_NAMES)
        concurrent_deployments = 5
        active_deployments = set(["diff-customer1", "diff-customer2"])
        num_active_deployemnts = len(active_deployments)
        expected_num_deployments = concurrent_deployments - num_active_deployemnts
        expected_customers_left_in_queue = total_in_queue - expected_num_deployments

        queue = self.setup_queue(queue_resource=self.hosted_root_sqs, add_msgs=True)
        customers_to_deploy = sorted(
            self.customer_deployment.get_customers_to_deploy_from_queue(
                active_deployments=active_deployments, num_concurrent_deployments=concurrent_deployments, queue=queue))
        assert customers_to_deploy == sorted(CUSTOMER_NAMES[:expected_num_deployments])
        assert int(queue.attributes["ApproximateNumberOfMessages"]) == expected_customers_left_in_queue

    def test_get_customers_to_deploy_from_queue_at_capacity_deploys_nothing(self):
        assert self.customer_deployment.get_customers_to_deploy_from_queue(active_deployments=range(10),
                                                                           num_concurrent_deployments=5,
                                                                           queue=None) == []

    def test_run_with_panther_root_and_hosted_root_true_runs_twice(self):
        customers_to_deploy = ["a", "b", "c"]
        self.mock_customer_deployment_funcs(customers_to_deploy)
        assert self.customer_deployment.run()["customers_deployed"] == customers_to_deploy + customers_to_deploy

    def test_get_aws_handles_returns_right_roles_for_panther_root(self):
        self.setup_queue(queue_resource=self.panther_root_sqs, add_msgs=True)
        handle = self.customer_deployment.get_aws_handles(include_panther_root=True, include_hosted_root=False)
        assert len(handle) == 1
        handle = handle[0]
        assert handle.ddb_name == "hosted-deployments-DeploymentMetadataTable-PXJR2DWAF84N"
        assert AccountId.PANTHER_ROOT in handle.sfn_arn
        assert "hosted-deployments-CertCreatorLambdaRole-8AALO976MRR5" in handle.cert_role_arn

    def test_get_aws_handles_returns_right_roles_for_hosted_root(self):
        self.setup_queue(queue_resource=self.hosted_root_sqs, add_msgs=True)
        handle = self.customer_deployment.get_aws_handles(include_panther_root=False, include_hosted_root=True)
        assert len(handle) == 1
        handle = handle[0]
        assert handle.ddb_name == "hosted-deployments-DeploymentMetadataTable-22PITRD2LM2B"
        assert AccountId.HOSTED_ROOT in handle.sfn_arn
        assert "hosted-deployments-CertCreatorLambdaRole-1KNU3G8ARXPYU" in handle.cert_role_arn

    def test_get_aws_handles_neither_hosted_root_or_panther_root_fails(self):
        with pytest.raises(ValueError):
            self.customer_deployment.get_aws_handles(include_panther_root=False, include_hosted_root=False)

    def test_get_aws_handles_panther_root_first_when_both_enabled(self):
        self.setup_queue(queue_resource=self.hosted_root_sqs, add_msgs=True)
        self.setup_queue(queue_resource=self.panther_root_sqs, add_msgs=True)
        handles = self.customer_deployment.get_aws_handles(include_panther_root=True, include_hosted_root=True)
        assert len(handles) == 2
        assert AccountId.PANTHER_ROOT in handles[0].sfn_arn
        assert AccountId.HOSTED_ROOT in handles[1].sfn_arn

    def test_given_customers_and_both_orgs_true_fails(self):
        with pytest.raises(ValueError):
            self.customer_deployment.get_aws_handles(include_panther_root=True,
                                                     include_hosted_root=True,
                                                     require_only_one=True)

    def test_deploy_now_customers(self):
        self.mock_customer_deployment_funcs(customers_to_deploy=[])
        deploy_now_customers = "customer-1, customer-2, customer-3"
        # Num concurrent deployments ignored when using deploy_now_customers
        deployed_customers = self.customer_deployment.run(
            num_concurrent_deployments=1, include_hosted_root=True,
            deploy_now_customers=deploy_now_customers)["customers_deployed"]
        assert deployed_customers == ["customer-1", "customer-2", "customer-3"]
