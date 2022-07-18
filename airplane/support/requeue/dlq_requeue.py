# Linked to https://app.airplane.dev/t/dlq_requeue [do not edit this line]

import json

from pyshared.aws_consts import get_aws_const
from pyshared.aws_creds import get_credentialed_client


def main(params):
    account_id = params["aws_account_id"].strip()
    from_queue = params["from_queue"].strip()
    to_queue = params.get("to_queue", "").strip()
    region = params["region"].strip()

    client_kwargs = {
        "arns":
        (get_aws_const("CUSTOMER_SUPPORT_ROLE_ARN"), f"arn:aws:iam::{account_id}:role/PantherSupportRole-{region}"),
        "region": region,
        "desc": "airplane_dlq"
    }

    if not to_queue:
        to_queue = get_to_queue(from_queue, client_kwargs)
        print(f"Using to_queue '{to_queue}'")

    # Invoke ops-tool
    lambda_client = get_credentialed_client(service_name="lambda", **client_kwargs)
    response_payload = invoke(lambda_client, from_queue, to_queue)

    if "errorMessage" in response_payload:
        raise RuntimeError(f"The DQL lambda response had an error: {response_payload}")


def get_to_queue(from_queue, client_kwargs):
    sqs_client = get_credentialed_client(service_name="sqs", **client_kwargs)
    dlq_url = sqs_client.get_queue_url(QueueName=from_queue)["QueueUrl"]
    queue_urls = sqs_client.list_dead_letter_source_queues(QueueUrl=dlq_url)["queueUrls"]
    if len(queue_urls) != 1:
        raise RuntimeError(f"""Could not find the to queue!
There was not exactly one source queue from this DLQ.
Source queues found: {queue_urls}""")

    return _get_queue_name_from_queue_url(queue_urls[0])


def _get_queue_name_from_queue_url(url):
    return url.rsplit("/", 1)[1]


def invoke(client, from_queue, to_queue):
    request_payload = {'requeue': {'fromQueue': from_queue, 'toQueue': to_queue}}
    print("payload: ", request_payload)

    response_payload = None
    while not _is_finished(response_payload):
        response = client.invoke(
            FunctionName="panther-ops-tools",
            Payload=json.dumps(request_payload),
            InvocationType="RequestResponse",
        )
        response_payload = json.loads(response.get("Payload").read().decode())
        print(response_payload)

    return response_payload


def _is_finished(response_payload):
    if (response_payload is None) or _is_batch_request_too_long(response_payload):
        return False
    return True


def _is_batch_request_too_long(response_payload):
    return "BatchRequestTooLong" in response_payload.get("errorMessage", "")


if __name__ == "__main__":
    args = {
        # gainful-wapiti
        'aws_account_id': "335415977059",
        'from_queue': "panther-alerts-queue-dlq",
        'to_queue': "panther-alerts-queue",
        'region': "us-east-2",
    }
    main(args)
