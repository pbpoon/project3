# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-08 06:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0006_auto_20170608_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='importorder',
            name='finish_pay',
            field=models.BooleanField(default=False, verbose_name='完成付款'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='finish_pay',
            field=models.BooleanField(default=False, verbose_name='完成付款'),
        ),
    ]
