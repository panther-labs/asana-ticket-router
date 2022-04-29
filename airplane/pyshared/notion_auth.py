import notional
from notional.orm import connected_page

from pyshared.aws_secrets import get_secret_value


class NotionSession:
    _SESSION = None
    _PAGE = None

    def __init__(self):
        self._session = NotionSession._SESSION
        self._page = NotionSession._PAGE

    @property
    def session(self):
        if self._session is None:
            auth_token = get_secret_value("airplane/notion-auth-token")
            self._session = NotionSession._SESSION = notional.connect(auth=auth_token)
        return self._session

    @property
    def page(self):
        if self._page is None:
            self._page = NotionSession._PAGE = connected_page(session=self.session)
        return self._page
