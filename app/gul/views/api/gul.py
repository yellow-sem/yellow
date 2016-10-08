from rest_framework.views import APIView
from rest_framework.response import Response

from gul.data.session import IDP3Session
from gul.data.services import GulService
from gul.views.api import identity


class CoursesView(identity.ServiceMixin, APIView):

    session_class = IDP3Session
    service_class = GulService

    def get(self, request):
        return Response(self.service.courses())


class StudentsView(identity.ServiceMixin, APIView):

    session_class = IDP3Session
    service_class = GulService

    def get(self, request, course_id):
        return Response(
            self.service.members(course_id,
                                 GulService.MEMBER_TYPE_STUDENT))


class SupervisorsView(identity.ServiceMixin, APIView):

    session_class = IDP3Session
    service_class = GulService

    def get(self, request, course_id):
        return Response(
            self.service.members(course_id,
                                 GulService.MEMBER_TYPE_SUPERVISOR))


class AssignmentsView(identity.ServiceMixin, APIView):

    session_class = IDP3Session
    service_class = GulService

    def get(self, request, course_id):
        return Response(self.service.assignments(course_id))
