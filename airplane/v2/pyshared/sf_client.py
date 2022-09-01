from typing import Any, List

import snowflake.connector

from pyshared.aws_secrets import get_snowflake_account_admin_secret


def get_account_admin_client():
    default_parent_account = "kma45798"
    default_region = "us-east-1"
    default_sf_url = "snowflakecomputing.com"

    secret = get_snowflake_account_admin_secret()
    return snowflake.connector.connect(user=secret["SNOWFLAKE_USERNAME"],
                                       password=secret["SNOWFLAKE_CREDENTIAL"],
                                       account=default_parent_account,
                                       host=f"{default_parent_account}.{default_region}.{default_sf_url}")


def exec_sql_cmds(client, sql_cmds: List[str]) -> snowflake.connector.cursor.SnowflakeCursor:
    """Execute a list of sql commands on the client and return the response of the final command."""
    cursor = client.cursor()
    if not isinstance(sql_cmds, list):
        raise ValueError(f"sql_cmds must be a list, not a {type(sql_cmds)}")
    for cmd in sql_cmds:
        # We only save the result from the last SQL command.
        result = cursor.execute(cmd)
    return result


def parse_sql_results(result: snowflake.connector.cursor.SnowflakeCursor) -> List[dict[str, Any]]:
    """Parse a SQL command's results into a list of dicts.

    Each list item is a row in the SQL result.
    Each dict has keys for column names and values for that item's result for that attribute.
    """
    column_names = [column.name for column in result.description]
    data = result.fetchmany()
    return [dict(zip(column_names, row)) for row in data]
