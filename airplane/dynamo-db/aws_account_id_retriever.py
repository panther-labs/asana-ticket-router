# Linked to https://app.airplane.dev/t/get_from_dynamo_db [do not edit this line]
from customer_info_retriever import retrieve_info


def main(params):
    if params["airplane_test_run"]:
        return {"aws_account_id": "123456789012"}

    return {"aws_account_id": retrieve_info(
        fairytale_name=params["fairytale_name"],
        customer_query_keys=("AWSConfiguration", "AccountId")
    )}
