import json

from boto3.dynamodb.conditions import Attr

from pyshared.aws_consts import get_aws_const
from pyshared.dynamo_db import DynamoDbSearch
from v2.task_models.airplane_task import AirplaneTask


class DeprovInfoRetriever(AirplaneTask):
    EXISTS_ATTR = "DeprovisionStatus"
    NO_EXISTS_ATTR = "DeprovisionDate"

    def run(self, params: dict):
        return self._parse_results(self._get_unparsed_results())

    def _get_unparsed_results(self):
        results = {}

        tables_and_arns = [(get_aws_const(const_name="HOSTED_DEPLOYMENTS_METADATA"),
                            get_aws_const(const_name="HOSTED_DYNAMO_RO_ROLE_ARN")),
                           (get_aws_const(const_name="STAGING_DEPLOYMENTS_METADATA"),
                            get_aws_const(const_name="ROOT_DYNAMO_RO_ROLE_ARN"))]

        for table_name, arn in tables_and_arns:
            db_search = DynamoDbSearch(table_name=table_name, arn=arn)
            filter_expr = (Attr(self.EXISTS_ATTR).exists()) & Attr(self.NO_EXISTS_ATTR).not_exists()
            results = {
                **results,
                **db_search.scan_and_organize_result(scan_result_keys=("CustomerId", ), filter_expr=filter_expr)
            }

        return results

    def _parse_results(self, db_search_results):
        return {
            fairytale_name: self._stringify_values(value[self.EXISTS_ATTR])
            for fairytale_name, value in db_search_results.items()
        }

    @staticmethod
    def _stringify_values(result_dict):
        return json.loads(json.dumps(result_dict, default=str))


def main(_):
    return DeprovInfoRetriever().run({})
