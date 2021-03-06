# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-09 08:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_merge_20170607_2301'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='batch',
            name='category',
        ),
        migrations.RemoveField(
            model_name='batch',
            name='quarry',
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='products.Category', verbose_name='品种名称'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='quarry',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='products.Quarry', verbose_name='矿口'),
            preserve_default=False,
        ),
    ]
