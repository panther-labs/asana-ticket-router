from botocore.exceptions import ClientError

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client
from pyshared.dynamo_db import DynamoDbSearch
from v2.exceptions import DomainNameAlreadyInUseException, FairytaleNameAlreadyInUseException


class NameValidator:
    CFN_RO_ROLE_ARN = get_aws_const("CLOUDFORMATION_READ_ONLY_ROLE_ARN")
    DDB_METADATA_TABLE = get_aws_const("HOSTED_DEPLOYMENTS_METADATA")
    DDB_RO_ROLE_ARN = get_aws_const("HOSTED_DYNAMO_RO_ROLE_ARN")

    def __init__(self):
        self.ddb_search = None

    def _get_ddb_search_instance(self):
        return self.ddb_search if self.ddb_search else DynamoDbSearch(table_name=self.DDB_METADATA_TABLE,
                                                                      arn=self.DDB_RO_ROLE_ARN)

    @staticmethod
    def _does_route53_record_exist_with_domain_name(domain_name):
        """Starting the record name and limiting to one will do one of two things:
            If the record exists, it will get that record, and that will be the one retrieved (and we raise an error)
            If the record doesn't exist, it will get a random one that won't match our domain name
        """
        client = get_credentialed_client(service_name="route53",
                                         arns=get_aws_const("HOSTED_ROUTE53_RO_ROLE_ARN"),
                                         desc=f"checking_route53_domains")

        record_name = client.list_resource_record_sets(HostedZoneId=get_aws_const("RUN_PANTHER_HOSTED_ZONE"),
                                                       StartRecordName=domain_name,
                                                       MaxItems="1")["ResourceRecordSets"][0]["Name"]

        return domain_name in record_name

    def _validate_domain_name(self, domain_name):
        if self._does_route53_record_exist_with_domain_name(domain_name):
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
