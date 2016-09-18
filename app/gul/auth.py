from urllib.parse import urlencode
from xml import etree

import requests
from social.backends.base import BaseAuth


class CAS3Auth(BaseAuth):

    LOGIN_URL = ''
    VALIDATE_URL = ''

    EXTRA_DATA = [
        ('username', 'username'),
        ('ticket', 'ticket'),
    ]

    def auth_url(self):
        return '{}?{}'.format(self.LOGIN_URL, urlencode({
            'service': self.redirect_uri,
        }))

    def auth_complete(self, *args, **kwargs):
        kwargs.update({
            'backend': self,
            'response': self.data,
        })

        return self.strategy.authenticate(*args, **kwargs)

    def get_user_id(self, details, response):
        return details.get('username')

    def get_user_details(self, response):
        ticket = response.get('ticket')

        data = {
            'ticket': ticket,
        }

        response = requests.get('{}?{}'.format(self.VALIDATE_URL, urlencode({
            'ticket': ticket,
            'service': self.redirect_uri,
        })))

        root = etree.ElementTree.fromstring(response.text)

        try:
            auth = next(node for node in root
                        if 'authenticationSuccess' in node.tag)
            user = next(node for node in auth
                        if 'user' in node.tag)

            data.update({
                'username': user.text,
            })
        except StopIteration:
            pass

        return data


class GUAuth(CAS3Auth):
    """Gothenburg University"""

    name = 'gu'

    LOGIN_URL = 'https://login.it.gu.se/login'
    VALIDATE_URL = 'https://login.it.gu.se/serviceValidate'


class DUAuth(CAS3Auth):
    """Dalarna University"""

    name = 'du'

    LOGIN_URL = 'https://login.du.se/cas/login'
    VALIDATE_URL = 'https://login.du.se/cas/serviceValidate'


class KAUAuth(CAS3Auth):
    """Karlstad University"""

    name = 'kau'

    LOGIN_URL = 'https://cas.kau.se/login'
    VALIDATE_URL = 'https://cas.kau.se/serviceValidate'


class KTHAuth(CAS3Auth):
    """Royal Institute of Technology"""

    name = 'kth'

    LOGIN_URL = 'https://login.kth.se/login'
    VALIDATE_URL = 'https://login.kth.se/serviceValidate'


class LIUAuth(CAS3Auth):
    """Linköping University"""

    name = 'liu'

    LOGIN_URL = 'https://login.liu.se/cas/login'
    VALIDATE_URL = 'https://login.liu.se/cas/serviceValidate'


class LTUAuth(CAS3Auth):
    """Luleå University of Technology"""

    name = 'ltu'

    LOGIN_URL = 'https://weblogon.ltu.se/casfirst/login'
    VALIDATE_URL = 'https://weblogon.ltu.se/casfirst/serviceValidate'


class LUAuth(CAS3Auth):
    """Lund University"""

    name = 'lu'

    LOGIN_URL = 'https://cas.lu.se/cas/login'
    VALIDATE_URL = 'https://cas.lu.se/cas/serviceValidate'


class UMUAuth(CAS3Auth):
    """Umeå University"""

    name = 'umu'

    LOGIN_URL = 'https://cas.umu.se/login'
    VALIDATE_URL = 'https://cas.umu.se/serviceValidate'
