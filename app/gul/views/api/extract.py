from rest_framework.views import APIView
from rest_framework.response import Response

from gul.data.session import IDP3Session
from gul.data.services import GulService
from gul.views.api import identity


class ExtractView(identity.ServiceMixin, APIView):

    session_class = IDP3Session
    service_class = GulService

    def get(self, request):
        return Response()
