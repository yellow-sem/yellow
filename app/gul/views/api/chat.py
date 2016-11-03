import re

from django.utils.functional import SimpleLazyObject

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from gul.data.session import IDP3Session, CAS3Session
from gul.data.services import GulService, LadokService
from gul.views.api import identity


class HandleView(identity.SessionMixin, APIView):

    session_class = CAS3Session

    class Serializer(serializers.Serializer):
        text = serializers.CharField(required=True)

    def perform_authentication(self, request):
        super().perform_authentication(request)

        self.gul = SimpleLazyObject(lambda: (
            identity.ServiceMixin.get_service(self,
                                              session_class=IDP3Session,
                                              service_class=GulService)
        ))

        self.ladok = SimpleLazyObject(lambda: (
            identity.ServiceMixin.get_service(self,
                                              session_class=CAS3Session,
                                              service_class=LadokService)
        ))

    def post(self, request):
        serializer = self.Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data.get('text')

        return Response({
            'text': self.handle(text),
        })

    def handle(self, text):
        if 'courses' in text:
            courses = self.gul.courses()
            return '<br/>'.join(['Your courses are:'] + [
                '{} ({})'.format(course['name'],
                                 {True: 'active',
                                  False: 'not active'}[course['active']])
                for course in sorted(courses,
                                     key=lambda course: (course['active'],
                                                         course['name']))
            ])

        if 'grade' in text:
            try:
                [code] = re.findall('([a-z]{3}-?[0-9]{3})', text.lower())
                code = code.replace('-', '')
            except ValueError:
                return 'Provide a course code in the format DIT-NNN.'

            courses = self.ladok.courses()
            try:
                course = next(course for course in courses
                              if course['code'].lower() == code)

                if course['grade']:
                    return 'You got {} for {} ({} credits)'.format(
                        course['grade'],
                        course['name'],
                        course['credits'],
                    )
                else:
                    return '{} has not been graded yet.'.format(course['name'])
            except StopIteration:
                return 'Course {} not found.'.format(code)

        return 'I have no idea what to do.'


class RoomsView(identity.ServiceMixin, APIView):

    session_class = IDP3Session
    service_class = GulService

    def get(self, request):
        return Response()
