# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-09 09:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('process', '0008_remove_slablist_order_item'),
    ]

    operations = [
        migrations.RenameField(
            model_name='slablistitem',
            old_name='item',
            new_name='slablist',
        ),
    ]