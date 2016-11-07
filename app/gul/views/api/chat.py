import re

from django.utils.functional import SimpleLazyObject
from django.utils.html import escape
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from gul.data.session import IDP3Session, CAS3Session
from gul.data.services import GulService, LadokService
from gul.views.api import identity
from gul.models import Room


class BaseView(identity.SessionMixin, APIView):

    session_class = CAS3Session

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


class HandleView(BaseView):

    class Serializer(serializers.Serializer):
        text = serializers.CharField(required=True)
        room_id = serializers.UUIDField(required=False)

    def post(self, request):
        serializer = self.Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data.get('text')
        room_id = serializer.validated_data.get('room_id')

        if room_id:
            try:
                room = Room.objects.get(room_id=room_id)
            except Room.DoesNotExist:
                room = None
        else:
            room = None

        text = self.handle(text.lower(), room=room)

        return Response({
            'text': escape(text).replace('\n', '<br/>'),
        })

    def handle(self, text, room=None):

        if room:
            if 'find' in text:
                text = text.replace('find', '').strip()

                students = [student for student in self.gul.members(
                    room.course_id,
                    GulService.MEMBER_TYPE_STUDENT
                ) if text in student['name'].lower()]

                supervisors = [supervisor for supervisor in self.gul.members(
                    room.course_id,
                    GulService.MEMBER_TYPE_SUPERVISOR,
                ) if text in supervisor['name'].lower()]

                if not students and not supervisors:
                    return 'Could not find anybody.'

                return '\n'.join(['Found:'] + [
                    ('Student: {} <{}@yellow>.'
                     .format(student['name'],
                             student['alias']))
                    for student in students
                ] + [
                    ('Supervisor: {} <{}@yellow>.'
                     .format(supervisor['name'],
                             supervisor['alias']))
                    for supervisor in supervisors
                ])

            if 'supervisors' in text:
                supervisors = self.gul.members(
                    room.course_id,
                    GulService.MEMBER_TYPE_SUPERVISOR,
                )

                return '\n'.join(['Supervisors for this course:'] + [
                    '{} <{}@yellow>'.format(supervisor['name'],
                                            supervisor['alias'])
                    for supervisor in
                    sorted(supervisors,
                           key=lambda supervisor: supervisor['name'])
                ])

            return 'I know it\'s {}, that\'s it.'.format(room.course_name)

        if 'courses' in text:
            courses = self.gul.courses()
            if not courses:
                return 'Could not find any courses.'

            return '\n'.join(['Your courses are:'] + [
                '{} ({})'.format(course['name'],
                                 {True: 'active',
                                  False: 'not active'}[course['active']])
                for course in sorted(courses,
                                     key=lambda course: (course['active'],
                                                         course['name']))
            ])

        if 'find course' in text:
            courses = self.gul.courses()
            if not courses:
                return 'Could not find any courses.'

            text = text.replace('find course', '').strip()

            courses = [course for course in courses
                       if text in course['name'].lower()]

            if not courses:
                return 'Course containing \'{}\' not found.'.format(text)

            return '\n'.join(['Courses found: '] + [
                '{} found {}'.format(
                    course['name'],
                    course['url'],
                ) for course in courses
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

        if 'supervisors' in text:
            try:
                [code] = re.findall('([a-z]{3}-?[0-9]{3})', text.lower())
                _code = code
                code = code.replace('-', '')
            except ValueError:
                return 'Provide a course code in the format DIT-NNN.'

            courses = self.gul.courses()
            if not courses:
                return 'Could not find any courses.'

            try:
                course = next(course for course in courses
                              if code in course['name'].lower())

                supervisors = self.gul.members(
                    course['id'],
                    GulService.MEMBER_TYPE_SUPERVISOR,
                )

                return '\n'.join([
                    'Supervisors for {}:'.format(course['name'])
                ] + [
                    '{} <{}@yellow>'.format(supervisor['name'],
                                            supervisor['alias'])
                    for supervisor in
                    sorted(supervisors,
                           key=lambda supervisor: supervisor['name'])
                ])

            except StopIteration:
                return 'Course {} not found.'.format(code)

        if 'find' in text:
            try:
                [code] = re.findall('([a-z]{3}-?[0-9]{3})', text.lower())
                _code = code
                code = code.replace('-', '')
            except ValueError:
                return 'Provide a course code in the format DIT-NNN.'

            courses = self.gul.courses()
            if not courses:
                return 'Could not find any courses.'

            try:
                course = next(course for course in courses
                              if code in course['name'].lower())

                text = text.replace('find', '')
                text = text.replace('in {}'.format(_code), '')
                text = text.strip()

                students = [student for student in self.gul.members(
                    course['id'],
                    GulService.MEMBER_TYPE_STUDENT
                ) if text in student['name'].lower()]

                supervisors = [supervisor for supervisor in self.gul.members(
                    course['id'],
                    GulService.MEMBER_TYPE_SUPERVISOR,
                ) if text in supervisor['name'].lower()]

                if not students and not supervisors:
                    return 'Could not find anybody.'

                return '\n'.join(['Found:'] + [
                    ('Student: {} <{}@yellow>.'
                     .format(student['name'],
                             student['alias']))
                    for student in students
                ] + [
                    ('Supervisor: {} <{}@yellow>.'
                     .format(supervisor['name'],
                             supervisor['alias']))
                    for supervisor in supervisors
                ])
            except StopIteration:
                return 'Course {} not found.'.format(code)

        if 'assignments' in text:
            try:
                [code] = re.findall('([a-z]{3}-?[0-9]{3})', text.lower())
                _code = code
                code = code.replace('-', '')
            except ValueError:
                return 'Provide a course code in the format DIT-NNN.'

            courses = self.gul.courses()
            if not courses:
                return 'Could not find any courses.'

            try:
                course = next(course for course in courses
                              if code in course['name'].lower())

                assignments = self.gul.assignments(course['id'])

                return '\n\n'.join([
                    'Assignments for {}:'.format(course['name'])
                ] + [
                    '{} {}\nGroup: {}\n{}'.format(
                        assignment['name'],
                        assignment['url'],
                        assignment['group'],
                        'due {}'.format(assignment['deadline'])
                        if assignment['status'] in (
                            GulService.ASSIGNMENT_STATUS_PENDING,
                            GulService.ASSIGNMENT_STATUS_RESUBMIT,
                        ) else assignment['status']
                    )
                    for assignment in
                    sorted(assignments,
                           key=lambda assignment: assignment['id'])
                ])

            except StopIteration:
                return 'Course {} not found.'.format(code)

        return 'I have no idea what to do.'


class RoomsView(BaseView):

    session_class = IDP3Session
    service_class = GulService

    def get(self, request):
        courses = self.gul.courses()

        Room.insert_if_not_exist([
            Room(
                course_id=course.get('id'),
                course_name=course.get('name'),
            )
            for course in courses
        ])

        return Response([{
            'id': str(room.room_id),
            'name': '{} ({})'.format(room.course_name,
                                     room.course_id),
        } for room in Room.objects.filter(
            course_id__in=[course.get('id') for course in courses]
        )])
