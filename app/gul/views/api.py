from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response

from utils.token import generate_token
from gul.data.session import Credentials, Session
from gul.models import Identity


class IdentityLoginView(APIView):
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


class IdentityLogoutView(APIView):
    """Logout from GU."""


class IdentityMixin(object):
    """Mixin for views that require a GU identity."""
