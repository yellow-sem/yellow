from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView

from gul.views import api


api_v1 = [
    url(r'identity/', include([
        url(r'login/', api.identity.LoginView.as_view(), name='login'),
        url(r'logout/', api.identity.LogoutView.as_view(), name='logout'),
    ], namespace='identity')),

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

    url(r'grades/$',
        api.ladok.CoursesView.as_view(),
        name='courses'),

    url(r'extract/$',
        api.extract.ExtractView.as_view(),
        name='extract'),

    url(r'chat/', include([
        url(r'handle/', api.chat.HandleView.as_view(), name='handle'),
        url(r'rooms/', api.chat.RoomsView.as_view(), name='rooms'),
    ], namespace='chat')),
]


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/auth/', include('rest_framework.urls', namespace='rest')),
    url(r'^api/v1/', include(api_v1, namespace='api_v1')),
    url(r'^auth/', include('social.apps.django_app.urls', namespace='social')),
]
