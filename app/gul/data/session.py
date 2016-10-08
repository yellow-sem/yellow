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

        data = {}

        data.update({
            'username': self.username,
            'password': self.password,
        })

        data.update({
            'j_username': self.username,
            'j_password': self.password,
            '_eventId_proceed': '',
        })

        return data


class Session(object):
    """Session with authenticated GU user."""

    KEY = NotImplemented

    def __init__(self, session=None):
        self.session = session or requests.Session()

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

        raise NotImplementedError()

    def logout(self):
        """Logout from session."""

        raise NotImplementedError()

    ########
    # DATA #
    ########

    DATA_COOKIES = 'cookies'
    DATA_HEADERS = 'headers'

    def to_data(self):
        return {
            self.KEY: {
                self.DATA_COOKIES: data_from_cookiejar(self.session.cookies),
                self.DATA_HEADERS: dict(self.session.headers),
            }
        }

    @classmethod
    def from_data(cls, data):
        data = data.get(cls.KEY)

        cookies = cookiejar_from_data(data.get(cls.DATA_COOKIES))
        headers = data.get(cls.DATA_HEADERS)

        session = requests.Session()
        session.cookies = cookies
        session.headers = headers
        return cls(session=session)

    def copy(self):
        return self.from_data(self.to_data())

    @classmethod
    def all_to_data(cls, *sessions):
        data = {}
        for session in sessions:
            data.update(session.to_data())
        return data


class CAS3Session(Session):

    KEY = 'cas3'

    BASE = 'https://login.it.gu.se'

    PATH_LOGIN = '/login'
    PATH_LOGOUT = '/logout'

    def login(self, credentials):

        url = urljoin(self.BASE, self.PATH_LOGIN)

        response = self.get(url)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        form = document.find('form')
        url = urljoin(response.url, form['action'])

        data = {}
        for field in form.select('input[name]'):
            data[field['name']] = field['value']

        data.update(credentials.data())

        response = self.post(url, data)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        return bool(document.select('[href="http://portalen.gu.se/student"]'))

    def logout(self):

        url = urljoin(self.BASE, self.PATH_LOGOUT)

        response = self.get(url)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        return bool(document.select('[href="http://portalen.gu.se/student"]'))


class IDP3Session(Session):

    KEY = 'idp3'

    BASE = 'https://gul.gu.se'

    PATH_LOGIN = '/login/processlogin'
    PATH_LOGOUT = '/logout.do'

    def login(self, credentials):

        url = urljoin(self.BASE, self.PATH_LOGIN)

        response = self.get(url)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        form = document.find('form')
        url = urljoin(response.url, form['action'])

        data = {}
        for field in form.select('input[name]'):
            data[field['name']] = field['value']

        data.update(credentials.data())

        response = self.post(url, data)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        form = document.find('form')
        url = form['action']

        data = {}
        for field in form.select('input[name]'):
            data[field['name']] = field['value']

        response = self.post(url, data)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        return bool(document.select('[href="/logout.do"]'))

    def logout(self):

        url = urljoin(self.BASE, self.PATH_LOGOUT)

        response = self.get(url)
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        return bool(document.select('.cas-logout'))
