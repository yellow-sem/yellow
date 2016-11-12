from urllib.parse import urljoin
import functools

import requests
import bs4

from gul.data.services.base import Service


class LadokService(Service):

    NAME = 'ladok'
    HOST = 'lpw.it.gu.se'
    BASE = 'http://{}/uPortal/Login'.format(HOST)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.courses = functools.lru_cache()(self.courses)

    def host(self):
        return self.HOST

    def url(self):
        return self.BASE

    ###########
    # SERVICE #
    ###########

    def courses(self):

        response = self.session.get(
            urljoin(self.BASE,
                    '/uPortal/f/u30l1s517/p/TG02.u30l1n616/max/render.uP'))

        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')

        data = []

        for row in document.select('.lpw-table tbody.parentBody > tr'):
            td = row.select('td')

            code = td[1]
            name = td[3]
            credits = td[4]
            grade = td[6]

            data.append({
                'code': code.text.strip(),
                'name': name.text.strip(),
                'credits': float(credits.text.strip()),
                'grade': grade.text.strip()
            })

        return data
