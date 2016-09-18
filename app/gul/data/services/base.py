from urllib.parse import urlparse

import requests


class Service(object):

    NAME = NotImplemented

    def __init__(self, session=None):
        self.session = session

    def host(self):
        raise NotImplementedError()

    def url(self):
        raise NotImplementedError()

    def valid(self):
        raise NotImplementedError()

    ########
    # AUTH #
    ########

    def login(self, session):
        """Login to service with the specified session."""

        assert self.session is None

        session = session.copy()

        response = session.get(self.url())
        assert response.status_code == requests.codes.ok

        self.session = session

        return urlparse(response.url).hostname == self.host()

    def logout(self):
        """Logout from service."""

        assert self.session is not None

        self.session = None
