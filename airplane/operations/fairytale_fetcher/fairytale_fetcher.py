from pyshared.aws_consts import get_aws_const
from v2.task_models.airplane_task import AirplaneTask
from pyshared.dynamo_db import DynamoDbSearch


class FairytaleFetcher(AirplaneTask):
    DDB_RO_ROLE_ARN = get_aws_const("HOSTED_DYNAMO_RO_ROLE_ARN")
    DDB_METADATA_TABLE = get_aws_const("HOSTED_DEPLOYMENTS_METADATA")

    def run(self, sales_customer_id):
        results = DynamoDbSearch(table_name=self.DDB_METADATA_TABLE,
                                 arn=self.DDB_RO_ROLE_ARN).get_query_item(key="SalesCustomerId",
                                                                          val=sales_customer_id,
                                                                          gsi_name="SalesCustomerId-Index")
        return {"fairytale_name": results['CustomerId']}


def main(params: dict):
    sales_customer_id = params['sales_customer_id']
    return FairytaleFetcher().run(sales_customer_id)
