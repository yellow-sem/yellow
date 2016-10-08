from rest_framework.views import APIView
from rest_framework.response import Response

from gul.data.session import CAS3Session
from gul.data.services import LadokService
from gul.views.api import identity


class CoursesView(identity.ServiceMixin, APIView):

    session_class = CAS3Session
    service_class = LadokService

    def get(self, request):
        return Response(self.service.courses())
