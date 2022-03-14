# Linked to https://app.airplane.dev/t/ephemeral_statistics_xkj [do not edit this line]

from datetime import datetime, timedelta
import base64
import boto3
import json

from pyshared.aws_creds import get_credentialed_client

# Put the main logic of the task in the main function.
def main(params):
    lambda_client = get_credentialed_client(service_name="lambda",
                        arns="arn:aws:iam::292442345278:role/EphemeralDeploymentAdmin",
                        region="us-west-2",
                        desc="airplane")

    host_count = count(lambda_client, "SELECT count(*) FROM hosts")
    host_in_use_count = count(lambda_client, "SELECT count(*) FROM hosts where state = 1")
    host_in_cleanup = count(lambda_client, "SELECT count(*) FROM hosts where state = 2")

    open_prs_count = count(lambda_client, "SELECT count(*) FROM refs where github_state = 1")
    open_prs_without_hosts_count = count(lambda_client, "SELECT count(*) FROM refs where github_state = 1 and host_id is null")

    one_week = datetime.today() - timedelta(weeks=1)
    deployments_count = count(lambda_client, f"SELECT count(*) FROM deployments where created_at > '{one_week}'")
    deployments_success_count = count(lambda_client, f"SELECT count(*) FROM deployments where step_function_result = 'success' and created_at > '{one_week}'")
    deployments_failed_count = count(lambda_client, f"SELECT count(*) FROM deployments where step_function_result = 'failed' and created_at > '{one_week}'")

    return {
        "hosts": {
            "count":  host_count,
            "in_use":  host_in_use_count,
            "in_cleanup":  host_in_cleanup,
        },
        "prs": {
            "open": open_prs_count,
            "without_hosts": open_prs_without_hosts_count,
        },
        "deployments_past_week": {
            "count": deployments_count,
            "success": deployments_success_count,
            "failed": deployments_failed_count,
        }
    }

def count(client, query):
    output = invoke(client, query)
    return output[0].get("count", 0)

def invoke(client, query):
    message_bytes = query.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes).decode("utf-8")
    payload = {'sql': {'query': base64_bytes}}
    # print("query: ", query)

    response = client.invoke(
        FunctionName="ephemeral-deployments-admin-host",
        Payload=json.dumps(payload),
        InvocationType="RequestResponse",
    )

    res = response.get('Payload').read().decode()
    # print("res: ", res)
    res_json = json.loads(res)
    output = res_json.get("sql", {}).get("result", {})
    # print("output: ", output)
    return output

if __name__ == "__main__":
    print(main({}))
