import re

from django.core.exceptions import PermissionDenied

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response

from utils.token import generate_token
from utils.models import get_or_none
from gul.data.session import Credentials, Session, CAS3Session, IDP3Session
from gul.models import Identity, Authorization


class IdentityMixin(object):

    SESSION_CLASS = [
        CAS3Session,
        IDP3Session,
    ]


class LoginView(IdentityMixin, APIView):
    """Login to GU."""

    class Serializer(serializers.Serializer):

        username = serializers.CharField()
        password = serializers.CharField()

    serializer_class = Serializer

    def post(self, request):
        serializer = self.Serializer(data=request.data)

        if serializer.is_valid():
            username = serializer.data['username']
            password = serializer.data['password']

            credentials = Credentials(
                username=username,
                password=password,
            )

            sessions = []
            success = True

            for session_class in self.SESSION_CLASS:

                session = session_class()
                success = success and session.login(credentials)

                if success:
                    sessions.append(session)

            token = None

            if success:
                token = generate_token()

                kwargs = {
                    'alias': username,
                }

                Identity(**kwargs).insert_if_not_exists()
                Identity.objects.filter(**kwargs).update(
                    session=Session.all_to_data(*sessions),
                    token=token,
                )

            return Response({
                'success': success,
                'token': token,
            }, status=(status.HTTP_200_OK
                       if success else status.HTTP_403_FORBIDDEN))
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class LogoutView(IdentityMixin, APIView):
    """Logout from GU."""

    def post(self, request):

        authorization = request.META.get('HTTP_AUTHORIZATION', '')

        try:
            # Valid token
            (token,) = re.findall('Token ([a-f0-9]+)', authorization)
            identity = get_or_none(Identity, token=token) if token else None
            success = identity is not None

            if success:
                for session_class in self.SESSION_CLASS:
                    session = session_class.from_data(identity.session)
                    session.logout()

                identity.delete()

        except ValueError:
            # Invalid token
            success = False

        return Response({
            'success': success,
        }, status=(status.HTTP_200_OK
                   if success else status.HTTP_400_BAD_REQUEST))


class SessionMixin(IdentityMixin):
    """Mixin for views that require a GU identity."""

    session_class = None

    def perform_authentication(self, request):
        """Set identity from authorization token."""

        assert (self.session_class is None or
                self.session_class in self.SESSION_CLASS)

        authorization = request.META.get('HTTP_AUTHORIZATION', '')

        try:
            # Valid token
            (token,) = re.findall('Token ([a-f0-9]+)', authorization)
            identity = get_or_none(Identity, token=token) if token else None
            session = (self.session_class.from_data(identity.session)
                       if identity else None)

        except ValueError:
            # Invalid token
            token = None
            identity = None
            session = None

        self.identity = identity
        self.session = session


class ServiceMixin(SessionMixin):
    """Mixin for views that require access to a specific GU service."""

    service_class = NotImplemented

    def perform_authentication(self, request):
        """Initialize service from current identity."""

        super().perform_authentication(request)

        if not self.session:
            raise PermissionDenied()

        service = None

        authorization = get_or_none(Authorization,
                                    identity=self.identity,
                                    service=self.service_class.NAME)
        if authorization:
            session = self.session_class.from_data(authorization.session)
            service = self.service_class(session=session)
        else:
            service = self.service_class()
            success = service.login(self.session)

            if success:
                kwargs = {
                    'identity': self.identity,
                    'service': self.service_class.NAME,
                }

                Authorization(**kwargs).insert_if_not_exists()
                Authorization.objects.filter(**kwargs).update(
                    session=service.session.to_data(),
                )

        if not service:
            raise PermissionDenied()

        self.service = service
