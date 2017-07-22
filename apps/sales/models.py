from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.shortcuts import reverse

CUSTOMER_TYPE_CHOICES = (('personal', '个人'), ('company', '公司'))
CALL_CHOICES = (('mr', '先生'), ('ms', '女士'), ('cp', '公司'))
STATUS_CHOICES = (
    ('N', '新订单'),
    ('V', '核实'),
    ('F', '完成'),
    ('C', '关闭'),
    ('M', '修改过')
)
ORDER_TAG = 'SL'
UNIT_CHOICES = (
    ('m2', 'm2'),
    ('m3', 'm3'),
    ('ton', 'ton'),
)


class CustomerInfo(models.Model):
    type = models.CharField('客户类型', choices=CUSTOMER_TYPE_CHOICES,
                            max_length=12, default='personal')
    name = models.CharField('名称', max_length=20)
    call = models.CharField('称呼', choices=CALL_CHOICES, max_length=12, default='mr')
    telephone = models.CharField('联系电话', max_length=11, null=True, blank=True, unique=True)
    province = models.ForeignKey('Province', verbose_name='省份', null=True)
    city = models.ForeignKey('City', verbose_name='城市', null=True)
    # last_date = models.DateTimeField('最后交易日期', null=True, blank=True)
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry',
                                         verbose_name='数据录入人')
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '客户信息'
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return reverse('sales:customer_detail', args=[self.id])

    def __str__(self):
        return '{} {}'.format(self.name, self.get_call_display())


class Province(models.Model):
    id = models.SmallIntegerField('id', primary_key=True)
    name = models.CharField('名称', max_length=20)
    province_id = models.SmallIntegerField('省份id', help_text='用于与市级联动')

    class Meta:
        verbose_name = '省份列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class City(models.Model):
    id = models.SmallIntegerField('id', primary_key=True)
    name = models.CharField('名称', max_length=20)
    father_id = models.SmallIntegerField('对应省份id')

    class Meta:
        verbose_name = '城市列表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SalesOrder(models.Model):
    status = models.CharField('订单状态', max_length=1, choices=STATUS_CHOICES, default='N')
    order = models.CharField('订单号', max_length=16, unique=True, db_index=True, default='new')
    customer = models.ForeignKey('CustomerInfo', related_name='order', verbose_name='客户名称')
    province = models.ForeignKey('Province', verbose_name='省份')
    city = models.ForeignKey('City', verbose_name='城市')
    date = models.DateField('订单日期', db_index=True)
    handler = models.ForeignKey(User, related_name='%(class)s_handler', verbose_name='经办人')
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry',
                                         verbose_name='数据录入人')
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    verifier = models.ForeignKey(User, related_name='%(class)s_verifier', verbose_name='审核人')
    verify_date = models.DateField('审核日期', db_index=True)

    class Meta:
        verbose_name = '销售订单'
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        # 格式为 1703001
        date_str = datetime.now().strftime('%y%m')
        if self.order == 'new':
            try:
                last_order = max([item.order for item in
                                  SalesOrder.objects.all()])
                if date_str in last_order[2:6]:
                    value = ORDER_TAG + str(int(last_order[2:9]) + 1)
                else:
                    value = ORDER_TAG + date_str + '001'  # 新月份
            except Exception as e:
                value = ORDER_TAG + date_str + '001'  # 新记录
            finally:
                self.status = 'N'
                self.order = value
        super(SalesOrder, self).save(*args, **kwargs)

    def __str__(self):
        return self.order

    def get_absolute_url(self):
        return reverse('sales:order_detail', args=[self.id])


class SalesOrderItem(models.Model):
    block_num = models.ForeignKey('products.Product', related_name='sale', verbose_name='荒料编号')
    order = models.ForeignKey('SalesOrder', related_name='items', verbose_name='对应单号')
    part = models.SmallIntegerField('夹数', null=True, blank=True)
    pic = models.SmallIntegerField('件数')
    thickness = models.CharField('厚度', max_length=6, null=True, blank=True)
    quantity = models.DecimalField('数量', max_digits=6, decimal_places=2)
    unit = models.CharField('单位', max_length=4, choices=UNIT_CHOICES)
    price = models.DecimalField('单价', max_digits=9, decimal_places=2)

    class Meta:
        verbose_name = '销售订单明细'
        verbose_name_plural = verbose_name
