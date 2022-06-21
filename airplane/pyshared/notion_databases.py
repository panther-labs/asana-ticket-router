from notional import schema, types
from notional.orm import Property
from notional.text import FullColor

from pyshared.notion_auth import NotionSession


def create_rtf_value(text, url=None, color=FullColor.DEFAULT):
    data = {
        "type":
        "rich_text",
        "rich_text": [{
            "type": "text",
            "plain_text": text,
            "href": url,
            "text": {
                "content": text,
            },
            "annotations": {
                "color": color
            }
        }]
    }

    text_obj = data["rich_text"][0]
    if url:
        text_obj["text"]["link"] = {"url": url}
    return types.RichText.parse_obj(data)


def get_display_rtf_value(value: schema.RichText):
    value = value.rich_text[0]
    return f"[{value.plain_text}]({value.href})"


def are_text_objects_equal(notion_val: schema.RichText, update_val: schema.RichText) -> bool:
    return ((notion_val.text == update_val.text) and (notion_val.href == update_val.href)
            and (notion_val.annotations.color == update_val.annotations.color))


def create_date_time_value(updated_datetime):
    return types.Date(date={"start": str(updated_datetime)})


class AccountsDatabaseSchema:
    Fairytale_Name = Property("Fairytale Name", schema.Title())
    AWS_Account_ID = Property("AWS Account ID", schema.RichText())
    Backend = Property("Backend", schema.Select())
    Deploy_Group = Property("Deploy Group", schema.Select())
    Email = Property("Email", schema.Email())
    Legacy_Stacks = Property("Legacy Stacks?", schema.Checkbox())
    Account_Name = Property("Account Name", schema.RichText())
    Notes = Property("Notes", schema.RichText())
    PoC = Property("PoC?", schema.Checkbox())
    Region = Property("Region", schema.Select())
    Service_Type = Property("Service Type", schema.Select())
    Support_Role = Property("Support Role", schema.RichText())
    Upgraded = Property("Upgraded", schema.Date())
    Actual_Version = Property("Actual Version", schema.RichText())
    Expected_Version = Property("Expected Version", schema.RichText())
    AWS_Organization = Property("AWS Organization", schema.Select())
    Account_Info_Auto_Updated = Property("Account Info Auto-Updated", schema.Checkbox())
    Airplane_Creation_Link = Property("Airplane Creation Link", schema.URL())
    Airplane_Creation_Completed = Property("Airplane Creation Completed", schema.Checkbox())

    def is_deprovision(self):
        return self.Service_Type == "Deprovision"

    def is_self_hosted(self):
        return self.Service_Type == "Self Hosted"


def get_accounts_database():
    """Notion database class definitions requires authentication to be setup when instantiated (the page object below).
    Wrapping the class in a function allows that instantiation to occur outside the global scope."""

    class AccountsDatabase(AccountsDatabaseSchema, NotionSession().page, database="cc445b0819164efca9d281e8ea2efab7"):
        pass

    return AccountsDatabase
