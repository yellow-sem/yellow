from django.conf.urls import include, url
from django.contrib import admin

from gul.views import api, site


api_v1 = [
    url(r'identity/', include([
        url(r'login/', api.identity.LoginView.as_view(), name='login'),
        url(r'logout/', api.identity.LogoutView.as_view(), name='logout'),
    ], namespace='identity')),

    url(r'gul/', include([
        url(r'courses/$',
            api.gul.CoursesView.as_view(),
            name='courses'),
        url(r'courses/(?P<course_id>[^/]+)/students/$',
            api.gul.StudentsView.as_view(),
            name='students'),
        url(r'courses/(?P<course_id>[^/]+)/supervisors/$',
            api.gul.SupervisorsView.as_view(),
            name='supervisors'),
        url(r'courses/(?P<course_id>[^/]+)/assignments/$',
            api.gul.AssignmentsView.as_view(),
            name='assignments'),
    ], namespace='gul')),

    url(r'ladok/', include([
        url(r'courses/$',
            api.ladok.CoursesView.as_view(),
            name='courses'),
    ], namespace='ladok')),
]


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/auth/', include('rest_framework.urls', namespace='rest')),
    url(r'^api/v1/', include(api_v1, namespace='api_v1')),
    url(r'^auth/', include('social.apps.django_app.urls', namespace='social')),
]
