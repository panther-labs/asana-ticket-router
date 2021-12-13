# Linked to https://app.airplane.dev/t/new_panther_deploy_notion_record [do not edit this line]

import os
import notional
from notional import blocks, types
from notional.orm import Property, connected_page
import datetime
import pytz

auth_token = os.getenv("NOTION_AUTH_TOKEN")
notion = notional.connect(auth=auth_token)
AccountsDatabase = connected_page(session=notion)


class Task(AccountsDatabase, database="cc445b0819164efca9d281e8ea2efab7"):
    Fairytale_Name = Property("Fairytale Name", types.Title)
    AWS_Account_ID = Property("AWS Account ID", types.RichText)
    Backend = Property("Backend", types.SelectOne)
    Deploy_Group = Property("Deploy Group", types.SelectOne)
    Email = Property("Email", types.Email)
    Legacy_Stacks = Property("Legacy Stacks?", types.Checkbox)
    Name = Property("Name", types.RichText)
    PoC = Property("PoC?", types.Checkbox)
    Region = Property("Region", types.SelectOne)
    Service_Type = Property("Service Type", types.SelectOne)
    Support_Role = Property("Support Role", types.RichText)
    Upgraded = Property("Upgraded", types.Date)
    Version = Property("Version", types.SelectOne)
    AWS_Organization = Property("AWS Organization", types.SelectOne)


def main(params):
    print("parameters:", params)

    task = Task.create(
        Fairytale_Name=params["fairytale_name"],
        AWS_Account_ID=params["aws_account_id"],
        Backend=params["backend"],
        Deploy_Group="L",
        Email=params["email"],
        Name=params["customer_name"],
        PoC=params["poc"],
        Region=params["region"],
        Service_Type=params["service_type"],
        Support_Role=params["support_role"],
        Upgraded=datetime.datetime.now(pytz.timezone('US/Pacific')).date(),
        Version=params["version"],
        AWS_Organization="panther-hosted-root",
    )

    task.commit()

    # Return output https://docs.airplane.dev/tasks/outputs
    return params
