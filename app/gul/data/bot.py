import re
import functools

import Levenshtein

from django.utils.functional import SimpleLazyObject

from gul.data.services import GulService


class Command(object):
    """Chat command."""

    class Request(object):
        """Incoming message."""

        gul = None
        ladok = None

        def __init__(self, text, room=None):

            self.text = text
            self.room = room

            self.course = functools.lru_cache()(self.course)

        def use(self, **attrs):
            """Provide services."""

            for key, value in attrs.items():
                if hasattr(type(self), key):
                    setattr(self, key, value)
                else:
                    raise ValueError('Service `{}` not allowed'.format(key))

        def course(self):
            """Try to obtain a course."""

            assert self.gul is not None

            courses = SimpleLazyObject(lambda: self.gul.courses())

            try:
                [code] = re.findall('([a-z]{3}-?[0-9]{3})', self.text.lower())
                code = code.replace('-', '')
            except ValueError:
                code = None

            # Obtain course by code
            if code:
                try:
                    course = next(course for course in courses
                                  if code in course['name'].lower())
                    return course
                except StopIteration:
                    pass

            # Obtain course from active room
            if self.room:
                return {
                    'id': self.room.course_id,
                    'name': 'this course',
                }

            # Obtain course by name similarity
            try:
                course = next(iter(sorted(
                    courses,
                    key=lambda course: (
                        0 if course['active'] and sum([
                            word.lower() in course['name'].lower()
                            for word in self.text.split(' ')
                            if len(word) >= 3
                        ]) >= 2 else (
                            Levenshtein.distance(self.text.lower(),
                                                 course['name'].lower()) * {
                                True: 1,
                                False: 2,
                            }[course['active']]
                        )
                    ),
                )))
                return course
            except StopIteration:
                pass

            return None

    class Response(object):
        """Outgoing message."""

        def __init__(self, lines):
            self.text = '\n'.join(lines)

    def __init__(self):
        pass

    def handle(self, request):
        """Handle the specified request and return a response."""

        raise NotImplementedError()


class FindCourseCommand(Command):
    """Command to search courses."""

    @classmethod
    def extract_term(cls, text):
        """Extract search term."""
        try:
            [term] = re.findall('course (.*)$', text)
            return term
        except ValueError:
            return None

    def handle(self, request):

        if request.room and request.room.course_id:
            return None

        term = self.extract_term(request.text)

        # Require search term
        if not term:
            return None

        courses = request.gul.courses()
        courses = [
            course for course in courses
            if term.lower() in course['name'].lower()
        ]

        return self.Response(([
            'Courses containing \'{}\':'.format(term),
        ] + [
            course['name']
            for course in courses
        ]) if courses else ['No courses found.'])


class FindUserCommand(Command):
    """Command to search users in a course."""

    def format(self, member):
        return '{type} {name} <{alias}@yellow>'.format(
            type={
                GulService.MEMBER_TYPE_STUDENT: 'Student',
                GulService.MEMBER_TYPE_SUPERVISOR: 'Supervisor',
            }[member['type']],

            name=member['name'],
            alias=member['alias'],
        )

    @classmethod
    def extract_term(cls, text):
        """Extract search term."""
        try:
            [term] = re.findall('find (.*) in', text)
            return term
        except ValueError:
            pass

        try:
            [term] = re.findall('find (.*) limit', text)
            return term
        except ValueError:
            pass

        try:
            [term] = re.findall('find (.*)', text)
            return term
        except ValueError:
            return None

    @classmethod
    def extract_limit(cls, text):
        """Extract list limit."""
        try:
            [limit] = re.findall('limit ([0-9]+)', text)
            limit = int(limit)
            return limit
        except ValueError:
            return None

    @classmethod
    def get_members(cls, request):
        """Get list of members."""

        members = []

        # Request students
        members += request.gul.members(
            request.course()['id'],
            GulService.MEMBER_TYPE_STUDENT,
        )

        # Request supervisors
        members += request.gul.members(
            request.course()['id'],
            GulService.MEMBER_TYPE_SUPERVISOR,
        )

        return members

    def handle(self, request):

        term = self.extract_term(request.text)
        limit = self.extract_limit(request.text) or 4

        # Require search term and limit
        if not term or not limit:
            return None

        # Require a course
        if not request.course():
            return None

        # Obtain members in course
        members = self.get_members(request)

        # Try exact match against alias
        try:
            member = next(member for member in members
                          if member['alias'] == term)
            return self.Response([
                'Found alias {}.'.format(self.format(member)),
            ])
        except StopIteration:
            pass

        # Sort users by similarity between name and search term
        members = sorted(
            members,
            key=(lambda member: Levenshtein.jaro(term.lower(),
                                                 member['name'].lower())),
            reverse=True,
        )

        return self.Response([
            'Users in {} similar to \'{}\':'.format(request.course()['name'],
                                                    term),
        ] + [
            self.format(member)
            for member in members[:limit]
        ])


class SupervisorListCommand(Command):
    """Command to list supervisors in a course."""

    def handle(self, request):

        if 'supervisors' not in request.text.lower():
            return None

        # Require a course
        if not request.course():
            return None

        # Request supervisors
        supervisors = request.gul.members(
            request.course()['id'],
            GulService.MEMBER_TYPE_SUPERVISOR,
        )

        return self.Response([
            'Supervisors for {}:'.format(request.course()['name']),
        ] + [
            '{} <{}@yellow>'.format(supervisor['name'],
                                    supervisor['alias'])
            for supervisor in sorted(
                supervisors,
                key=lambda supervisor: supervisor['name']
            )
        ])


class CourseGradeCommand(Command):
    """Command to get the grade for a course."""

    def handle(self, request):

        if 'grade' not in request.text.lower():
            return

        # Require a course
        if not request.course():
            return None

        # Get course code
        try:
            [code] = re.findall('([a-z]{3}-?[0-9]{3})',
                                request.course()['name'].lower())
            code = code.replace('-', '')
        except ValueError:
            return None

        # Request courses
        courses = request.ladok.courses()

        try:
            course = next(course for course in courses
                          if course['code'].lower() == code)

            if course['grade']:
                text = 'You got {} for {} ({} credits)'.format(
                    course['grade'],
                    course['name'],
                    course['credits'],
                )
            else:
                text = '{} ({} credits) has not been graded yet.'.format(
                    course['name'], course['credits'])
        except StopIteration:
            text = 'Course {} not found.'.format(code)

        return self.Response([text])


class CourseAssignmentListCommand(Command):
    """Command to list assignments for a course."""

    def handle(self, request):

        if 'assignments' not in request.text.lower():
            return None

        # Require a course
        if not request.course():
            return None

        # Request assignments
        assignments = request.gul.assignments(request.course()['id'])

        return self.Response([
            'Assignments for {}:'.format(request.course()['name']),
        ] + [
            '\n{} {}\nGroup: {}\n{}'.format(
                assignment['name'],
                assignment['url'],
                assignment['group'] or 'Not set',
                'Due {}'.format(assignment['deadline'])
                if assignment['status'] in (
                    GulService.ASSIGNMENT_STATUS_PENDING,
                    GulService.ASSIGNMENT_STATUS_RESUBMIT,
                ) else assignment['status'].capitalize()
            )
            for assignment in
            sorted(assignments,
                   key=lambda assignment: assignment['id'])
        ])


class GradeListCommand(Command):
    """Command to list all grades."""

    def handle(self, request):

        if 'grades' not in request.text.lower():
            return

        # Request courses
        courses = request.ladok.courses()

        return self.Response([
            'Grades:'
        ] + [
            '{}: {} ({} credits)'.format(
                course['name'],
                course['grade'] or 'Not graded',
                course['credits'],
            )
            for course in courses
        ])


class HelpCommand(Command):
    """Command to show bot help."""

    def handle(self, request):

        if 'help' not in request.text.lower():
            return

        return self.Response([
            'Course room help:',
            'find {user}',
            'supervisors',
            'assignments',
        ] if request.room and request.room.course_id else [
            'General help:',
            'find course {course}',
            'find {user} in {course} [limit {limit}]',
            'supervisors for {course}',
            'grade for {course}',
            'assignments for {course}',
            'grades',
        ])


class Handler(object):

    def __init__(self, commands):
        self.commands = commands

    def handle(self, request):
        for command in self.commands:
            response = command.handle(request)
            if response:
                return response

        return Command.Response(['I have no idea what to do.'])


handler = Handler([
    SupervisorListCommand(),
    FindCourseCommand(),
    FindUserCommand(),
    GradeListCommand(),
    CourseGradeCommand(),
    CourseAssignmentListCommand(),
    HelpCommand(),
])
