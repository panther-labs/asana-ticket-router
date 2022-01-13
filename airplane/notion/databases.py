from notional import types
from notional.orm import Property


from notion.auth import page


def create_rtf_value(text, url=None):
    return types.RichText.parse_obj({
        "type": "rich_text",
        "rich_text": [{
            "type": "text",
            "plain_text": text,
            "text": {"content": text, "link": {"url": url}},
        }]
    })


def create_date_time_value(updated_datetime):
    return types.Date(date={"start": str(updated_datetime)})


class AccountsDatabase(page, database="cc445b0819164efca9d281e8ea2efab7"):
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
