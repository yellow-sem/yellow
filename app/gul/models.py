import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from utils import sql


class Identity(models.Model, sql.StandardIINEModelMixin):

    RELATED_NAME = 'identities'

    alias = models.CharField(_('alias'), max_length=100, unique=True)
    session = JSONField(_('session'), null=True, blank=True)
    token = models.CharField(_('token'), max_length=32, unique=True,
                             null=True, blank=True)

    class Meta:
        verbose_name = _('identity')
        verbose_name_plural = _('identities')


class Authorization(models.Model, sql.StandardIINEModelMixin):

    RELATED_NAME = 'authorizations'

    identity = models.ForeignKey(Identity, verbose_name=_('identity'),
                                 related_name=RELATED_NAME)
    service = models.CharField(_('service'), max_length=40)
    session = JSONField(_('session'), null=True, blank=True)

    class Meta:
        unique_together = (('identity', 'service'),)
        verbose_name = _('authorization')
        verbose_name_plural = _('authorizations')


class Room(models.Model, sql.StandardIINEModelMixin):

    RELATED_NAME = 'rooms'

    room_id = models.UUIDField(_('room ID'), default=uuid.uuid4,
                               editable=False)

    course_id = models.IntegerField(_('course ID'), unique=True)
    course_name = models.CharField(_('course name'), max_length=100)

    class Meta:
        verbose_name = _('room')
        verbose_name_plural = _('rooms')
