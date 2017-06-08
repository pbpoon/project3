# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-06 05:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_auto_20170604_2158'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, default=120, max_digits=9, verbose_name='单价'),
            preserve_default=False,
        ),
    ]