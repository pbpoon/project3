# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-04 03:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0011_auto_20170616_2258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='importorderitem',
            name='block_num',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='import_order', to='purchase.PurchaseOrderItem', verbose_name='荒料编号'),
        ),
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='block_num',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchase', to='products.Product', verbose_name='荒料编号'),
        ),
    ]
