# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-21 03:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0004_auto_20170720_2352'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customerinfo',
            name='last_date',
        ),
        migrations.AlterField(
            model_name='customerinfo',
            name='call',
            field=models.CharField(choices=[('mr', '先生'), ('ms', '女士'), ('cp', '公司')], default='mr', max_length=12, verbose_name='称呼'),
        ),
    ]