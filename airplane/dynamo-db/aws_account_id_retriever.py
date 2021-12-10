# Linked to https://app.airplane.dev/t/get_from_dynamo_db [do not edit this line]
from customer_info_retriever import retrieve_info


def main(params):
    return {"aws_account_id": retrieve_info(
        fairytale_name=params["fairytale_name"],
        customer_query_keys=("AWSConfiguration", "AccountId")
    )}
