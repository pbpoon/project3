# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-05 08:24
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0011_salesorder_is_proceeds'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesorder',
            name='verifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='salesorder_verifier', to=settings.AUTH_USER_MODEL, verbose_name='审核人'),
        ),
        migrations.AlterField(
            model_name='salesorder',
            name='verify_date',
            field=models.DateField(blank=True, null=True, verbose_name='审核日期'),
        ),
    ]