# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-19 02:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('process', '0009_auto_20170709_1737'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slablistitem',
            name='line_num',
            field=models.SmallIntegerField(blank=True, null=True, verbose_name='序号'),
        ),
    ]