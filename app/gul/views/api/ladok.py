from rest_framework.views import APIView
from rest_framework.response import Response

from gul.data.services import LadokService
from gul.views.api import identity


class CoursesView(identity.ServiceMixin, APIView):

    service = LadokService

    def get(self, request):
        return Response(request.service.courses())
