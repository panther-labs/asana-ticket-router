from notional import types
from notional.orm import Property

from pyshared.notion_auth import page


def create_rtf_value(text, url=None):
    return types.RichText.parse_obj({
        "type":
        "rich_text",
        "rich_text": [{
            "type": "text",
            "plain_text": text,
            "href": url,
            "text": {
                "content": text,
                "link": {
                    "url": url
                }
            },
        }]
    })


def get_display_rtf_value(value: types.RichText):
    value = value.rich_text[0]
    return f"[{value.plain_text}]({value.href})"


def are_rtf_values_equal(notion_val: types.RichText, update_val: types.RichText) -> bool:
    notion = notion_val.rich_text[0]
    update = update_val.rich_text[0]
    return (notion.text == update.text) and (notion.href == update.href)


def create_date_time_value(updated_datetime):
    return types.Date(date={"start": str(updated_datetime)})


class AccountsDatabase(page, database="cc445b0819164efca9d281e8ea2efab7"):
    Fairytale_Name = Property("Fairytale Name", types.Title)
    AWS_Account_ID = Property("AWS Account ID", types.RichText)
    Backend = Property("Backend", types.SelectOne)
    Deploy_Group = Property("Deploy Group", types.SelectOne)
    Email = Property("Email", types.Email)
    Legacy_Stacks = Property("Legacy Stacks?", types.Checkbox)
    Account_Name = Property("Account Name", types.RichText)
    Notes = Property("Notes", types.RichText)
    PoC = Property("PoC?", types.Checkbox)
    Region = Property("Region", types.SelectOne)
    Service_Type = Property("Service Type", types.SelectOne)
    Support_Role = Property("Support Role", types.RichText)
    Upgraded = Property("Upgraded", types.Date)
    Version = Property("Version", types.SelectOne)
    AWS_Organization = Property("AWS Organization", types.SelectOne)
    Account_Info_Auto_Updated = Property("Account Info Auto-Updated", types.Checkbox)
    Airplane_Creation_Completed = Property("Airplane Creation Completed", types.Checkbox)
