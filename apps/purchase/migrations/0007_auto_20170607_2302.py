# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-07 15:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0006_auto_20170607_2301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='importorderitem',
            name='block_num',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_order', to='purchase.PurchaseOrderItem', to_field='block_num', verbose_name='荒料编号'),
        ),
    ]
