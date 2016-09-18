from rest_framework.views import APIView
from rest_framework.response import Response

from gul.data.services import GulService
from gul.views.api import identity


class CoursesView(identity.ServiceMixin, APIView):

    service = GulService

    def get(self, request):
        return Response(request.service.courses())


class StudentsView(identity.ServiceMixin, APIView):

    service = GulService

    def get(self, request, course_id):
        return Response(
            request.service.members(course_id,
                                    GulService.MEMBER_TYPE_STUDENT))


class SupervisorsView(identity.ServiceMixin, APIView):

    service = GulService

    def get(self, request, course_id):
        return Response(
            request.service.members(course_id,
                                    GulService.MEMBER_TYPE_SUPERVISOR))


class AssignmentsView(identity.ServiceMixin, APIView):

    service = GulService

    def get(self, request, course_id):
        return Response(request.service.assignments(course_id))
