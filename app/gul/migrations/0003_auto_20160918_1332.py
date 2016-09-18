# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-18 13:32
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gul', '0002_auto_20160918_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='identity',
            name='token',
            field=models.CharField(blank=True, db_index=True, max_length=32, null=True, verbose_name='token'),
        ),
        migrations.AlterField(
            model_name='authorization',
            name='session',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='session'),
        ),
        migrations.AlterField(
            model_name='identity',
            name='session',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='session'),
        ),
    ]
