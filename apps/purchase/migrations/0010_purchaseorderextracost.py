# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-10 13:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchase', '0009_merge_20170609_1655'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseOrderExtraCost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.CharField(choices=[('travel', '差旅'), ('ticket', '机票'), ('discount', '折扣')], max_length=10, verbose_name='项目')),
                ('desc', models.CharField(blank=True, max_length=80, null=True, verbose_name='补充说明')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='金额')),
                ('date', models.DateField(verbose_name='日期')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '额外费用',
                'verbose_name_plural': '额外费用',
            },
        ),
    ]
