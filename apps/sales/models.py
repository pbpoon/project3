from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

CUSTOMER_TYPE_CHOICES = (('personal', '个人'), ('company', '公司'))
CALL_CHOICES = (('mr', 'Mr'), ('ms', 'Ms'), ('cp', '公司'))
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
    name = models.CharField('名称', max_length=20)
    type = models.CharField('客户类型', choices=CUSTOMER_TYPE_CHOICES,
                            max_length=12)
    call = models.CharField('称呼', choices=CALL_CHOICES,
                            max_length=12)
    telephone = models.CharField('联系电话', max_length=11, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry',
                                         verbose_name='数据录入人')
    province = models.ForeignKey('Province', verbose_name='省份')
    city = models.ForeignKey('City', verbose_name='城市')
    last_date = models.DateTimeField('最后交易日期', default=datetime.now)
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = '客户信息'
        verbose_name_plural = verbose_name


class Province(models.Model):
    name = models.CharField('名称', max_length=20)

    class Meta:
        verbose_name = '省份列表'
        verbose_name_plural = verbose_name


class City(models.Model):
    name = models.CharField('名称', max_length=20)

    class Meta:
        verbose_name = '城市列表'
        verbose_name_plural = verbose_name


class SalesOrder(models.Model):
    status = models.CharField('订单状态', max_length=1, choices=STATUS_CHOICES,
                              default='N')
    order = models.CharField('订单号', max_length=16, unique=True, db_index=True,
                             default='new')
    customer = models.ForeignKey('CustomerInfo', related_name='order', verbose_name='客户名称')
    province = models.ForeignKey('Province', verbose_name='省份')
    city = models.ForeignKey('City', verbose_name='城市')
    date = models.DateField('订单日期', db_index=True)
    handler = models.ForeignKey(User, related_name='%(class)s_handler',
                                verbose_name='经办人')
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry',
                                         verbose_name='数据录入人')
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    verifier = models.ForeignKey(User, related_name='%(class)s_handler', verbose_name='审核人')
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
                                  SalesOrder.objects.filter(
                                      order_type=ORDER_TAG)])
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


class SalesOrderItem(models.Model):
    block_num = models.ForeignKey('products.Product', related_name='sale', verbose_name='荒料编号')
    order = models.ForeignKey('SalesOrder', related_name='items', verbose_name='对应单号')
    part = models.SmallIntegerField('夹数', null=True, blank=True)
    pic = models.SmallIntegerField('件数', null=True, blank=True)
    thickness = models.CharField('厚度', max_length=6, null=True, blank=True)
    quantity = models.DecimalField('数量', max_digits=6, decimal_places=2)
    unit = models.CharField('单位', max_length=4, choices=UNIT_CHOICES)

    class Meta:
        verbose_name = '销售订单明细'
        verbose_name_plural = verbose_name