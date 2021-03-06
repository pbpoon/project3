# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-10 13:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_auto_20170609_1655'),
    ]

    operations = [
        migrations.CreateModel(
            name='Slab',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thick', models.DecimalField(db_index=True, decimal_places=2, max_digits=4, verbose_name='厚度')),
                ('part_num', models.CharField(max_length=8, verbose_name='夹号')),
                ('line_num', models.SmallIntegerField(verbose_name='序号')),
                ('long', models.PositiveSmallIntegerField(verbose_name='长')),
                ('high', models.PositiveSmallIntegerField(verbose_name='高')),
                ('kl1', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='长1')),
                ('kl2', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='长2')),
                ('kh1', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='高1')),
                ('kh2', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='高2')),
                ('m2', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='平方')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='添加日期')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='更新日期')),
                ('is_sell', models.BooleanField(default=False, verbose_name='是否已售')),
                ('is_booking', models.BooleanField(default=False, verbose_name='是否已定')),
                ('is_pickup', models.BooleanField(default=False, verbose_name='是否已提货')),
                ('block_num', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Product', verbose_name='荒料编号')),
            ],
        ),
    ]
