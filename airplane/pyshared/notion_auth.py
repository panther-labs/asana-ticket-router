import os
import notional
from notional.orm import connected_page

from pyshared.aws_secrets import get_secret_value

auth_token = get_secret_value("airplane/notion-auth-token")
notion_session = notional.connect(auth=auth_token)
page = connected_page(session=notion_session)
