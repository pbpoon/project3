# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-05 06:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0010_auto_20170728_1728'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesorder',
            name='is_proceeds',
            field=models.BooleanField(default=False, verbose_name='是否收款'),
        ),
    ]
