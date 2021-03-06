# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-04 13:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('purchase', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='block_num',
            field=models.OneToOneField(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='block', to='purchase.PurchaseOrderItem', to_field='block_num', verbose_name='荒料编号'),
        ),
        migrations.AddField(
            model_name='batch',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Category', verbose_name='品种名称'),
        ),
        migrations.AddField(
            model_name='batch',
            name='quarry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Quarry', verbose_name='矿口'),
        ),
    ]
