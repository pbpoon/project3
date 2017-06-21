# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-20 14:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('process', '0003_auto_20170620_1616'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ksorderitem',
            old_name='think',
            new_name='thickness',
        ),
        migrations.AddField(
            model_name='mborderitem',
            name='thickness',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=4, verbose_name='厚度'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='ksorderitem',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='金额'),
        ),
        migrations.AlterField(
            model_name='ksorderitem',
            name='line_num',
            field=models.SmallIntegerField(blank=True, null=True, verbose_name='序号'),
        ),
        migrations.AlterField(
            model_name='mborderitem',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='金额'),
        ),
        migrations.AlterField(
            model_name='mborderitem',
            name='line_num',
            field=models.SmallIntegerField(blank=True, null=True, verbose_name='序号'),
        ),
        migrations.AlterField(
            model_name='storderitem',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='金额'),
        ),
        migrations.AlterField(
            model_name='storderitem',
            name='line_num',
            field=models.SmallIntegerField(blank=True, null=True, verbose_name='序号'),
        ),
        migrations.AlterField(
            model_name='tsorderitem',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name='金额'),
        ),
        migrations.AlterField(
            model_name='tsorderitem',
            name='line_num',
            field=models.SmallIntegerField(blank=True, null=True, verbose_name='序号'),
        ),
    ]
