from urllib.parse import urljoin

import requests
import bs4

from gul.data.utils import data_from_cookiejar, cookiejar_from_data


class Credentials(object):
    """Auth credentials."""

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def data(self):
        return {
            'username': self.username,
            'password': self.password,
        }


class Session(object):
    """Session with authenticated GU user."""

    BASE = 'https://login.it.gu.se'

    PATH_LOGIN = '/login'
    PATH_LOGOUT = '/logout'

    def __init__(self, session=None):
        self.session = session or requests.Session()

    def url(self, path):
        return urljoin(self.BASE, path)

    def valid(self):
        raise NotImplementedError()

    ########
    # HTTP #
    ########

    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    ########
    # AUTH #
    ########

    def login(self, credentials):
        """Login with the specified credentials."""

        url = self.url(self.PATH_LOGIN)

        response = self.get(url)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        form = document.find('form')

        data = {}
        for field in form.select('input'):
            data[field['name']] = field['value']

        data.update(credentials.data())

        response = self.post(url, data)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        return bool(document.select('[href="http://portalen.gu.se/student"]'))

    def logout(self):
        """Logout from session."""

        url = self.url(self.PATH_LOGOUT)

        response = self.get(url)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        return bool(document.select('[href="http://portalen.gu.se/student"]'))

    ########
    # DATA #
    ########

    DATA_COOKIES = 'cookies'
    DATA_HEADERS = 'headers'

    def to_data(self):
        return {
            self.DATA_COOKIES: data_from_cookiejar(self.session.cookies),
            self.DATA_HEADERS: dict(self.session.headers),
        }

    @classmethod
    def from_data(cls, data):
        cookies = cookiejar_from_data(data.get(cls.DATA_COOKIES))
        headers = data.get(cls.DATA_HEADERS)

        session = requests.Session()
        session.cookies = cookies
        session.headers = headers
        return cls(session=session)

    def copy(self):
        return self.from_data(self.to_data())
