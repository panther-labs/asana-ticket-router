from pyshared.aws_consts import get_aws_const
from v2.task_models.airplane_task import AirplaneTask
from pyshared.dynamo_db import DynamoDbSearch
from v2.exceptions import SalesIdNotFoundException


class FairytaleFetcher(AirplaneTask):
    DDB_RO_ROLE_ARN = get_aws_const("HOSTED_DYNAMO_RO_ROLE_ARN")
    DDB_METADATA_TABLE = get_aws_const("HOSTED_DEPLOYMENTS_METADATA")

    def __init__(self):
        self.ddb_search = None

    def _get_ddb_search_instance(self):
        return self.ddb_search if self.ddb_search else DynamoDbSearch(table_name=self.DDB_METADATA_TABLE,
                                                                      arn=self.DDB_RO_ROLE_ARN)

    @staticmethod
    def _get_fairytale_from_query_results(results, sales_opportunity_id) -> str | None:
        for customer in results:
            if customer['SalesOpportunityId'] == sales_opportunity_id:
                return customer['CustomerId']

    def main(self, sales_customer_id, sales_opportunity_id) -> str:
        results = self._get_ddb_search_instance().get_query_items(key="SalesCustomerId",
                                                                  val=sales_customer_id,
                                                                  gsi_name="SalesCustomerId-Index")
        fairytale = self._get_fairytale_from_query_results(results, sales_opportunity_id)

        if fairytale:
            return fairytale
        else:
            raise SalesIdNotFoundException(
                f"ERROR: Unable to find customer with SalesCustomerId [{sales_customer_id}] and "
                f"SalesOpportunityId [{sales_opportunity_id}]")


def main(params: dict) -> dict:
    sales_customer_id = params['sales_customer_id']
    sales_opportunity_id = params['sales_opportunity_id']
    fairytale = FairytaleFetcher().main(sales_customer_id, sales_opportunity_id)
    return {"fairytale_name": fairytale}
