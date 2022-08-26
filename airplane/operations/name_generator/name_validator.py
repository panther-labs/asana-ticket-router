from pyshared import cloudformation_yaml
from pyshared.aws_consts import get_aws_const
from pyshared.dynamo_db import DynamoDbSearch
from v2.exceptions import DomainNameAlreadyInUseException, FairytaleNameAlreadyInUseException


class NameValidator:
    CFN_RO_ROLE_ARN = get_aws_const("CLOUDFORMATION_READ_ONLY_ROLE_ARN")
    DDB_METADATA_TABLE = get_aws_const("HOSTED_DEPLOYMENTS_METADATA")
    DDB_RO_ROLE_ARN = get_aws_const("HOSTED_DYNAMO_RO_ROLE_ARN")

    def __init__(self, active_domain_names=None):
        self.active_domain_names = self._populate_domain_names_in_use(
        ) if active_domain_names is None else active_domain_names
        self.ddb_search = None

    def _get_ddb_search_instance(self):
        return self.ddb_search if self.ddb_search else DynamoDbSearch(table_name=self.DDB_METADATA_TABLE,
                                                                      arn=self.DDB_RO_ROLE_ARN)

    def _validate_domain_name(self, domain_name):
        if domain_name in self.active_domain_names:
            raise DomainNameAlreadyInUseException(f"ERROR: Domain name [{domain_name}] already in use!")

    def _validate_fairytale_name(self, fairytale_name):
        results = self._get_ddb_search_instance().get_query_item(key="CustomerId", val=fairytale_name)

        if results.get('CustomerId') == fairytale_name:
            raise FairytaleNameAlreadyInUseException(f"ERROR: Fairytale name [{fairytale_name}] already in use!")

    def run_validation(self, domain_name, fairytale_name):
        self._validate_domain_name(domain_name)
        self._validate_fairytale_name(fairytale_name)
        print(f"INFO: Successfully validated domain [{domain_name}] and fairytale name [{fairytale_name}]!")
        return True

    def _get_domain_name_from_stack(self, stack):
        return cloudformation_yaml.get_cloudformation_physical_resource_id_from_stack(
            role_arn=self.CFN_RO_ROLE_ARN, stack_name=stack["StackName"], logical_resource_id="CustomerSubdomain")

    def _populate_domain_names_in_use(self):
        all_active_stacks = cloudformation_yaml.get_active_customer_instance_domain_stacks(self.CFN_RO_ROLE_ARN)
        return [self._get_domain_name_from_stack(stack) for stack in all_active_stacks]
