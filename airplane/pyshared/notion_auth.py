import os
import notional
from notional.orm import connected_page

auth_token = os.getenv("NOTION_AUTH_TOKEN")
notion_session = notional.connect(auth=auth_token)
page = connected_page(session=notion_session)
