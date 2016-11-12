from django.utils.functional import SimpleLazyObject
from django.utils.html import escape

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from gul.data.session import IDP3Session, CAS3Session
from gul.data.services import GulService, LadokService
from gul.data.bot import Command, handler
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
        request = Command.Request(text, room=room)
        request.use(
            gul=self.gul,
            ladok=self.ladok,
        )
        response = handler.handle(request)
        return response.text


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
