from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from gul.data.session import IDP3Session
from gul.data.services import GulService
from gul.views.api import identity


class HandleView(identity.ServiceMixin, APIView):

    session_class = IDP3Session
    service_class = GulService

    class Serializer(serializers.Serializer):
        text = serializers.CharField(required=True)

    def post(self, request):
        serializer = self.Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data.get('text')
        text = '{} from bot'.format(text)

        return Response({
            'text': text,
        })


class RoomsView(identity.ServiceMixin, APIView):

    session_class = IDP3Session
    service_class = GulService

    def get(self, request):
        return Response()
