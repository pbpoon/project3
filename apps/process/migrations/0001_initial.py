# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-10 14:09
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0007_slab'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='KSOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_num', models.SmallIntegerField(default=1, verbose_name='序号')),
                ('block_type', models.CharField(choices=[('block', '荒料'), ('coarse', '毛板'), ('slab', '板材')], default='block', max_length=6, verbose_name='形态')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='数量')),
                ('price', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='价格')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='金额')),
                ('date', models.DateField(default='django.utils.timezone.now', verbose_name='日期')),
                ('ps', models.CharField(blank=True, max_length=100, null=True, verbose_name='备注信息')),
                ('pic', models.SmallIntegerField(blank=True, null=True, verbose_name='件数')),
                ('pi', models.SmallIntegerField(blank=True, null=True, verbose_name='板皮')),
                ('unit', models.CharField(default='m3', max_length=2, verbose_name='单位')),
                ('block_num', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ksorderitem_cost', to='products.Product', verbose_name='荒料编号')),
            ],
            options={
                'verbose_name': '界石加工单',
                'verbose_name_plural': '界石加工单',
            },
        ),
        migrations.CreateModel(
            name='MBOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_num', models.SmallIntegerField(default=1, verbose_name='序号')),
                ('block_type', models.CharField(choices=[('block', '荒料'), ('coarse', '毛板'), ('slab', '板材')], default='block', max_length=6, verbose_name='形态')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='数量')),
                ('price', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='价格')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='金额')),
                ('date', models.DateField(default='django.utils.timezone.now', verbose_name='日期')),
                ('ps', models.CharField(blank=True, max_length=100, null=True, verbose_name='备注信息')),
                ('pic', models.SmallIntegerField(blank=True, null=True, verbose_name='件数')),
                ('unit', models.CharField(default='m2', max_length=2, verbose_name='单位')),
                ('block_num', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mborderitem_cost', to='products.Product', verbose_name='荒料编号')),
            ],
            options={
                'verbose_name': '补板加工单',
                'verbose_name_plural': '补板加工单',
            },
        ),
        migrations.CreateModel(
            name='ProcessOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('N', '新订单'), ('V', '核实'), ('F', '完成'), ('C', '关闭'), ('M', '修改过')], default='N', max_length=1, verbose_name='订单状态')),
                ('order_type', models.CharField(choices=[('TS', '运输'), ('MB', '补板'), ('KS', '界石'), ('ST', '到货')], max_length=2, verbose_name='订单类型')),
                ('order', models.CharField(db_index=True, default='new', max_length=16, unique=True, verbose_name='订单号')),
                ('date', models.DateField(db_index=True, verbose_name='订单日期')),
                ('service_provider_order', models.CharField(blank=True, max_length=20, null=True, verbose_name='对方单号')),
                ('ps', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注信息')),
                ('created', models.DateField(auto_now_add=True, verbose_name='创建日期')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('data_entry_staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='processorder_entry', to=settings.AUTH_USER_MODEL, verbose_name='数据录入人')),
                ('handler', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='processorder_handler', to=settings.AUTH_USER_MODEL, verbose_name='经办人')),
            ],
            options={
                'verbose_name': '加工订单',
                'verbose_name_plural': '加工订单',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='ServiceProvider',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=80, unique=True, verbose_name='名称')),
                ('service_type', models.CharField(choices=[('TS', '运输'), ('MB', '补板'), ('KS', '界石'), ('ST', '到货')], max_length=2, verbose_name='服务类型')),
                ('default_price', models.DecimalField(decimal_places=2, default=0, max_digits=9, verbose_name='默认单价')),
                ('unit', models.CharField(choices=[('m2', 'm2'), ('m3', 'm3'), ('che', '车'), ('ton', 'ton')], max_length=4, verbose_name='单位')),
                ('address', models.CharField(blank=True, max_length=100, null=True, verbose_name='地址')),
                ('desc', models.CharField(blank=True, max_length=200, null=True, verbose_name='补充说明')),
                ('contacts', models.CharField(blank=True, max_length=8, null=True, verbose_name='联系人')),
                ('telephone', models.CharField(blank=True, max_length=11, null=True, verbose_name='联系电话')),
                ('created', models.DateField(auto_now_add=True, verbose_name='创建日期')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '服务商信息',
                'verbose_name_plural': '服务商信息',
            },
        ),
        migrations.CreateModel(
            name='SlabList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('thick', models.DecimalField(db_index=True, decimal_places=2, max_digits=4, verbose_name='厚度')),
                ('ps', models.CharField(blank=True, max_length=200, null=True, verbose_name='备注信息')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='添加日期')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='更新日期')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('data_entry_staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='date_entry', to=settings.AUTH_USER_MODEL, verbose_name='数据录入人')),
                ('order_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slablist', to='process.MBOrderItem', verbose_name='荒料编号')),
            ],
            options={
                'verbose_name': '码单信息',
                'verbose_name_plural': '码单信息',
                'ordering': ['-updated'],
            },
        ),
        migrations.CreateModel(
            name='SlabListItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('part_num', models.CharField(max_length=8, verbose_name='夹号')),
                ('line_num', models.SmallIntegerField(verbose_name='序号')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='item', to='process.SlabList', verbose_name='对应码单')),
                ('slab', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Slab', verbose_name='板材编号')),
            ],
        ),
        migrations.CreateModel(
            name='STOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_num', models.SmallIntegerField(default=1, verbose_name='序号')),
                ('block_type', models.CharField(choices=[('block', '荒料'), ('coarse', '毛板'), ('slab', '板材')], default='block', max_length=6, verbose_name='形态')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='数量')),
                ('price', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='价格')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='金额')),
                ('date', models.DateField(default='django.utils.timezone.now', verbose_name='日期')),
                ('ps', models.CharField(blank=True, max_length=100, null=True, verbose_name='备注信息')),
                ('block_num', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='storderitem_cost', to='products.Product', verbose_name='荒料编号')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='storderitem', to='process.ProcessOrder', verbose_name='加工订单号')),
            ],
            options={
                'verbose_name': '荒料到货单',
                'verbose_name_plural': '荒料到货单',
            },
        ),
        migrations.CreateModel(
            name='TSOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_num', models.SmallIntegerField(default=1, verbose_name='序号')),
                ('block_type', models.CharField(choices=[('block', '荒料'), ('coarse', '毛板'), ('slab', '板材')], default='block', max_length=6, verbose_name='形态')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='数量')),
                ('price', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='价格')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='金额')),
                ('date', models.DateField(default='django.utils.timezone.now', verbose_name='日期')),
                ('ps', models.CharField(blank=True, max_length=100, null=True, verbose_name='备注信息')),
                ('unit', models.CharField(default='车', max_length=1, verbose_name='单位')),
                ('be_from', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='TS_from', to='process.ServiceProvider')),
                ('block_num', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tsorderitem_cost', to='products.Product', verbose_name='荒料编号')),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='TS_to', to='process.ServiceProvider')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tsorderitem', to='process.ProcessOrder', verbose_name='加工订单号')),
            ],
            options={
                'verbose_name': '运输单',
                'verbose_name_plural': '运输单',
            },
        ),
        migrations.AddField(
            model_name='processorder',
            name='service_provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='process.ServiceProvider', verbose_name='服务商'),
        ),
        migrations.AddField(
            model_name='mborderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mborderitem', to='process.ProcessOrder', verbose_name='加工订单号'),
        ),
        migrations.AddField(
            model_name='ksorderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ksorderitem', to='process.ProcessOrder', verbose_name='加工订单号'),
        ),
    ]
