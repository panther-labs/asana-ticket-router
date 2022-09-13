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
    AWS_Account_Deleted = Property("Account Deleted?", schema.Select())
    AWS_Account_ID = Property("AWS Account ID", schema.RichText())
    AWS_Organization = Property("AWS Organization", schema.Select())
    Account_Info_Auto_Updated = Property("Account Info Auto-Updated", schema.Checkbox())
    Account_Name = Property("Account Name", schema.RichText())
    Actual_Version = Property("Actual Version", schema.RichText())
    Airplane_Creation_Completed = Property("Airplane Creation Completed", schema.Checkbox())
    Airplane_Creation_Link = Property("Airplane Creation Link", schema.URL())
    Backend = Property("Backend", schema.Select())
    DNS_Records_Removed = Property("DNS Records Removed?", schema.RichText())
    Deploy_Group = Property("Deploy Group", schema.Select())
    Deployment_File_Removed = Property("Deployment File Removed?", schema.RichText())
    Email = Property("Email", schema.Email())
    Expected_Version = Property("Expected Version", schema.RichText())
    Fairytale_Name = Property("Fairytale Name", schema.Title())
    Legacy_Stacks = Property("Legacy Stacks?", schema.Checkbox())
    Master_Stack_Removed = Property("Master Stack Removed?", schema.RichText())
    Moved_To_Suspended_OU = Property("Moved to Suspended OU?", schema.RichText())
    Notes = Property("Notes", schema.RichText())
    PoC = Property("PoC?", schema.Checkbox())
    Region = Property("Region", schema.Select())
    SF_Account_Deleted = Property("SF Account Deleted?", schema.Select())
    SF_Account_Case_Number = Property("SF Account Case Number", schema.RichText())
    SF_Account_Name_Locator = Property("SF Account Name / Locator", schema.RichText())
    Sentry_Alerts_Disabled = Property("Sentry Alerts Disabled?", schema.Select())
    Service_Type = Property("Service Type", schema.Select())
    Support_Role = Property("Support Role", schema.RichText())
    Upgraded = Property("Upgraded", schema.Date())

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
