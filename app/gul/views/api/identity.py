import re

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response

from utils.token import generate_token
from utils.models import get_or_none
from gul.data.session import Credentials, Session
from gul.models import Identity


class Mixin(object):
    """Mixin for views that require a GU identity."""

    def perform_authentication(self, request):
        """Set identity from authorization token."""

        authorization = request.META.get('HTTP_AUTHORIZATION', '')

        try:
            # Valid token
            (token,) = re.findall('Token ([a-f0-9]+)', authorization)
            identity = get_or_none(Identity, token=token) if token else None
            session = Session.from_data(identity.session) if identity else None

        except ValueError:
            # Invalid token
            token = None
            identity = None
            session = None

        request.identity = identity
        request.session = session


class LoginView(Mixin, APIView):
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

            session = Session()
            success = session.login(credentials)
            token = None

            if success:
                token = generate_token()

                kwargs = {'alias': username}
                Identity(**kwargs).insert_if_not_exists()
                Identity.objects.filter(**kwargs).update(
                    session=session.to_data(),
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


class LogoutView(Mixin, APIView):
    """Logout from GU."""

    def post(self, request):
        if request.session:
            request.session.logout()

            request.identity.session = None
            request.identity.token = None
            request.identity.save(update_fields=('session', 'token'))

            success = True
        else:
            success = False

        return Response({
            'success': success,
        }, status=(status.HTTP_200_OK
                   if success else status.HTTP_403_FORBIDDEN))


class ServiceMixin(Mixin):
    """Mixin for views that require access to a specific GU service."""

    service = NotImplemented
