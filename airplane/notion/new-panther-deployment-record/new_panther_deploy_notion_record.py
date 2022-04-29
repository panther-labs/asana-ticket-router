import datetime
import pytz

from pyshared.notion_databases import get_accounts_database


def get_backend(backend):
    return {"Managed": "Managed SF"}.get(backend, backend)


def main(params):
    customer = params["account_name"]
    fairytale = params["fairytale_name"]
    region = params["region"]
    aws_account_id = params["aws_account_id"]
    support_role = params["support_role"]
    support_link = f'https://{region}.signin.aws.amazon.com/switchrole?roleName={support_role}&account={aws_account_id}&displayName={customer}%20Support'
    support_value = f'[{support_role}]({support_link})'

    task = get_accounts_database().create(
        Fairytale_Name=fairytale,
        AWS_Account_ID=params["aws_account_id"],
        Backend=get_backend(params["backend"]),
        Deploy_Group="L",
        Email=params["email"],
        Account_Name=params["account_name"],
        PoC=params["poc"],
        Region=region,
        Service_Type=params["service_type"],
        Support_Role=support_value,
        Upgraded=datetime.datetime.now(pytz.timezone('US/Pacific')).date(),
        Version=params["version"],
        AWS_Organization="panther-hosted-root",
    )

    if params["airplane_test_run"]:
        task.Service_Type = "Airplane Testing"

    # Return output https://docs.airplane.dev/tasks/outputs
    return params
