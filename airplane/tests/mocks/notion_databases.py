from pyshared.notion_databases import AccountsDatabaseSchema

# Fake Notion database. They can't be instantiated without connecting to Notion; this class can. This creates a
# dynamic class with the same attributes, assuming they are all strings (which isn't true, but is good enough for now)
MockAccountsDatabase: AccountsDatabaseSchema = type(
    "MockAccountsDatabase", (object, ), {
        attr_name: ""
        for attr_name in dir(AccountsDatabaseSchema) if isinstance(getattr(AccountsDatabaseSchema, attr_name), property)
    })
