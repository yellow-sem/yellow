# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-18 12:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gul', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identity',
            name='alias',
            field=models.CharField(max_length=100, unique=True, verbose_name='alias'),
        ),
        migrations.AlterUniqueTogether(
            name='authorization',
            unique_together=set([('identity', 'service')]),
        ),
    ]