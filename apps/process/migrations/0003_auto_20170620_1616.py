# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-20 08:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('process', '0002_auto_20170616_2258'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ksorderitem',
            name='block_type',
        ),
        migrations.RemoveField(
            model_name='mborderitem',
            name='block_type',
        ),
        migrations.RemoveField(
            model_name='storderitem',
            name='block_type',
        ),
    ]
