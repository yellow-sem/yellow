from django.conf.urls import include, url
from django.contrib import admin

from gul.views import api, site


api_v1 = [
    url(r'identity/', include([
        url(r'login/', api.IdentityLoginView.as_view(), name='login'),
        url(r'logout/', api.IdentityLogoutView.as_view(), name='logout'),
    ], namespace='identity')),
]


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/auth/', include('rest_framework.urls', namespace='rest')),
    url(r'^api/v1/', include(api_v1, namespace='api_v1')),
    url(r'^auth/', include('social.apps.django_app.urls', namespace='social')),
]
