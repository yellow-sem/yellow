import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlencode

import requests
import bs4
from dateutil.parser import parse
from pytz import timezone

from gul.data.services.base import Service


class GulService(Service):

    NAME = 'gul'
    HOST = 'gul.gu.se'
    BASE = 'https://{}/login/processlogin'.format(HOST)
    TARGET = '/startPage.do'

    def host(self):
        return self.HOST

    def url(self):
        return '{}?{}'.format(self.BASE, urlencode({
            'targeturl': self.TARGET,
        }))

    ###########
    # SERVICE #
    ###########

    def courses(self):

        response = self.session.get(urljoin(self.BASE, '/listCourses.do'))
        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')

        data = []

        for row in document.select('#myCourses .data-row'):
            td = row.select('td')

            name = td[1].find('a')
            href = name['href']
            id = int(re.findall('id=([0-9]*)', href)[0])
            name = name.text

            group = td[2].find('span')
            group = group.text

            active = td[4]
            active = active.text.lower().strip()
            active = active in ('visible', 'synlig')

            if group.lower() == 'supportaktiviteter':
                continue

            data.append({
                'id': id,
                'name': name,
                'category': group,
                'active': active,
                'url': urljoin(self.BASE, href),
            })

        return data

    MEMBER_TYPE_STUDENT = 'participant'
    MEMBER_TYPE_SUPERVISOR = 'teacher'

    def members(self, course_id, member_type):
        """Get the list of members in the specified course."""

        response = self.session.get('{}?{}'.format(
            urljoin(self.BASE,
                    '/courseId/{}/courseParticipants.do'.format(course_id)),
            urlencode({
                'tableCurrentPageparticipantList': 0,
                'listType': member_type,
                'tablePageSizeparticipantList': 100,
            }),
        ))

        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')

        data = []

        for row in document.select('#participantList .data-row'):
            td = row.select('td')

            first_name = td[1].text
            last_name = td[2].text
            alias = td[3].text.split('@')[0]

            data.append({
                'name': '{} {}'.format(first_name, last_name),
                'alias': alias,
            })

        return data

    ASSIGNMENT_STATUS_PENDING = 'pending'
    ASSIGNMENT_STATUS_MARKING = 'marking'
    ASSIGNMENT_STATUS_RESUBMIT = 'resubmit'
    ASSIGNMENT_STATUS_RESUBMITTED = 'resubmitted'
    ASSIGNMENT_STATUS_COMPLETED = 'completed'

    def assignments(self, course_id):
        """Get the list of assignments from the specified course."""

        response = self.session.get(
            urljoin(self.BASE,
                    '/courseId/{}/contentStart.do'.format(course_id)))

        assert response.status_code == requests.codes.ok

        document = bs4.BeautifulSoup(response.text, 'html.parser')

        data = []

        for content in document.select('#courseMainBox .treeNodeText'):
            a = content.find('a')
            href = a['href']
            id = int(re.findall('id=([0-9]*)', href)[0])
            name = a.text

            response = self.session.get(
                urljoin(
                    self.BASE,
                    ('/pp/courses/course{}/published/0/resourceId/0'
                     '/content/contentFrame.do?id={}').format(course_id, id)))
            if response.status_code != requests.codes.ok:
                continue

            document = bs4.BeautifulSoup(response.text, 'html.parser')
            submission = document.select('#ppReportSubmission')
            if not submission:
                continue

            submission = submission[0]

            group = submission.find('h2').text.strip()

            prompt = submission.select('.rsPrompt')[0]
            prompt = prompt.decode_contents(formatter='html')

            fields = {
                'id': id,
                'name': name,
                'group': group if 'group' in group.lower() else None,
                'url': urljoin(self.BASE, href),
            }

            match = re.findall(
                '<strong>(.*):<\/strong>[\n\r\s]*(.*)[\n\r\s]*<br\/>',
                str(submission.select('.rsBox')[0])
            )

            for label, text in match:
                label = label.lower().strip()
                text = text.lower().strip()

                if label in ('status', 'status'):

                    value = None

                    if text in ('not yet submitted',
                                'ej inlämnad'):
                        value = self.ASSIGNMENT_STATUS_PENDING

                    if text in ('to be marked', 'ogranskad'):
                        value = self.ASSIGNMENT_STATUS_MARKING

                    if text in ('revision required',
                                'kompletteras'):
                        value = self.ASSIGNMENT_STATUS_RESUBMIT

                    if text in ('revision submitted',
                                'komplettering inlämnad'):
                        value = self.ASSIGNMENT_STATUS_RESUBMITTED

                    if text in ('completed', 'färdig'):
                        value = self.ASSIGNMENT_STATUS_COMPLETED

                    fields['status'] = value

                if label in ('submission deadline',
                             'sista tidpunkt för inlämning'):

                    value = None

                    text = text.replace('maj', 'may')
                    if ',' in text:
                        text = text.split(',')[0]

                    try:
                        value = parse(text)
                    except ValueError:
                        match = re.findall('([^\s]*) ([0-9]+:[0-9]+)', text)
                        if match:
                            date, time = None, None

                            date_text, time_text = match[0]
                            date_text = date_text.lower().strip()

                            now = datetime.now(timezone('Europe/Stockholm'))

                            if date_text in ('today', 'idag'):
                                date = now.date()

                            if date_text in ('yesterday', 'igår'):
                                date = (now - timedelta(days=1)).date()

                            time = parse(time_text).time()

                            value = datetime.combine(date, time)

                    fields['deadline'] = value

            data.append(fields)

        return data
