from gul.data.services.base import Service


class AccountService(Service):

    NAME = 'acc'
    HOST = 'konto.gu.se'
    BASE = 'https://{}/gus/myPassword.php'.format(HOST)

    def host(self):
        return self.HOST

    def url(self):
        return self.BASE
