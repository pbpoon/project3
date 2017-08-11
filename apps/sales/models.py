from collections import defaultdict
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.shortcuts import reverse
from decimal import Decimal

CUSTOMER_TYPE_CHOICES = (('personal', '个人'), ('company', '公司'))
CALL_CHOICES = (('mr', '先生'), ('ms', '女士'), ('cp', '公司'))
STATUS_CHOICES = (
    ('N', '新订单'),  # new
    ('V', '核实'),  # verify
    ('F', '完成'),  # finish
    ('C', '关闭'),  # closed
    ('M', '修改过')  # modification
)
ORDER_TAG = 'SL'
UNIT_CHOICES = (
    ('m2', 'm2'),
    ('m3', 'm3'),
    ('ton', 'ton'),
)
SALES_PROCEEDS_TYPE = (
    ('E', '订金'),  # earnest money
    ('G', '货款')  # payment of goods
)
SALES_PROCEEDS_METHOD = (
    ('T', '转账'),  # transfer account
    ('C', '现金'),  # cash
    ('B', '冲账'),  # strike a balance
)
SALES_ORDER_PICK_UP_COST = (
    ('P', '打木夹'),
    ('L', '裝车'),
    ('M', '木方'),
    ('O', '其它')
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
    is_proceeds = models.BooleanField('是否收款', default=False)
    order = models.CharField('订单号', max_length=16, unique=True, db_index=True, default='new')
    customer = models.ForeignKey('CustomerInfo', related_name='order', verbose_name='客户名称')
    province = models.ForeignKey('Province', verbose_name='省份')
    city = models.ForeignKey('City', verbose_name='城市')
    date = models.DateField('订单日期', db_index=True)
    handler = models.ForeignKey(User, related_name='%(class)s_handler', verbose_name='经办人')
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry', verbose_name='数据录入人')
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    verifier = models.ForeignKey(User, related_name='%(class)s_verifier', verbose_name='审核人', null=True)
    verify_date = models.DateField('审核日期', null=True, blank=True)
    slab_list = GenericRelation('process.SlabList')

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

    def get_total_quantity_of_can_pickup(self):
        return '{:.2f}'.format(sum(sum(item.total_quantity().values()) for item in self.pickup.all()))

    def get_total_quantity(self):
        dt = defaultdict(float)
        for item in self.items.all():
            dt[item.unit] += float(item.quantity)
        return {k: float(v) for k, v in dt.items()}

    def sum_total_quantity(self):
        return '{:.2f}'.format(sum(self.get_total_quantity().values()))

    def _get_pickup_progress(self):
        a = Decimal(self.sum_total_quantity())
        b = Decimal(self.get_total_quantity_of_can_pickup())
        return format((a - (a - b)) / a, '0.1%')
    pickup_progress = property(_get_pickup_progress)

    def _get_total_amount(self):
        return '{:.2f}'.format(sum(Decimal(item.sum) for item in self.items.all()))

    amount = property(_get_total_amount)

    def _get_total_proceeds(self):
        return '{:.2f}'.format(sum(Decimal(item.amount) for item in self.proceeds.all()))
    proceeds = property(_get_total_proceeds)

    def _get_balance(self):
        return '{:.2f}'.format(Decimal(self._get_total_amount())-Decimal(self._get_total_proceeds()))

    balance = property(_get_balance)


class SalesOrderItem(models.Model):
    block_num = models.ForeignKey('products.Product', related_name='sale', verbose_name='荒料编号')
    order = models.ForeignKey('SalesOrder', related_name='items', verbose_name='对应单号')
    part = models.SmallIntegerField('夹数', null=True, blank=True)
    pic = models.SmallIntegerField('件数')
    thickness = models.CharField('厚度', max_length=6, null=True, blank=True)
    quantity = models.DecimalField('数量', max_digits=6, decimal_places=2)
    unit = models.CharField('单位', max_length=4, choices=UNIT_CHOICES)
    price = models.DecimalField('单价', max_digits=6, decimal_places=0)

    class Meta:
        verbose_name = '销售订单明细'
        verbose_name_plural = verbose_name

    def _get_sum(self):
        return '{:.0f}'.format(self.quantity * self.price)

    sum = property(_get_sum)


class SalesProceeds(models.Model):
    order = models.ForeignKey('SalesOrder', related_name='proceeds', on_delete=models.CASCADE,
                              verbose_name='对应销售单')
    amount = models.DecimalField('金额', max_digits=9, decimal_places=0)
    type = models.CharField('款项类型', max_length=1, choices=SALES_PROCEEDS_TYPE, default='g')
    method = models.CharField('支付方式', choices=SALES_PROCEEDS_METHOD, max_length=1)
    account = models.ForeignKey('ProceedsAccount', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name='收款账户')
    date = models.DateField('支付日期', db_index=True)
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry', verbose_name='数据录入人')
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '销售订单收款记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '[{}]:{}'.format(self.order, self.amount)

    def get_absolute_url(self):
        return reverse('sales:proceeds_detail', args=[self.id])


class ProceedsAccount(models.Model):
    name = models.CharField('账户名称', max_length=20, unique=True)
    bank_name = models.CharField('银行名称', max_length=10)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '账户信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{}-{}'.format(self.bank_name, self.name)

    def get_absolute_url(self):
        return reverse('sales:account_detail', args=[self.id])


class SalesOrderPickUp(models.Model):
    order = models.ForeignKey('SalesOrder', related_name='pickup', on_delete=models.CASCADE,
                              verbose_name='对应销售单')
    cart_num = models.CharField('提货车牌', max_length=10)
    consignee = models.CharField('提货人', max_length=10)
    date = models.DateField('提货日期', db_index=True)
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry',
                                         verbose_name='数据录入人')
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    slab_list = GenericRelation('process.SlabList')

    class Meta:
        verbose_name = '销售提货单'
        verbose_name_plural = verbose_name
        ordering = ['date']

    def __str__(self):
        return '[{}]'.format(self.order)

    def get_absolute_url(self):
        return reverse('sales:pickup_detail', args=[self.id])

    def total_quantity(self):
        dt = defaultdict(float)
        for item in self.items.all():
            dt[item.unit] += float(item.quantity)
        return {k: float(v) for k, v in dt.items()}

    def total_cost(self):
        return '{:.2f}'.format(sum(item.amount for item in self.cost.all()))


class SalesOrderPickUpItem(models.Model):
    block_num = models.ForeignKey('products.Product', related_name='pickup_item',
                                  verbose_name='荒料编号')
    order = models.ForeignKey('SalesOrderPickUp', related_name='items', verbose_name='对应单号')
    part = models.SmallIntegerField('夹数', null=True, blank=True)
    pic = models.SmallIntegerField('件数')
    thickness = models.CharField('厚度', max_length=6, null=True, blank=True)
    quantity = models.DecimalField('数量', max_digits=6, decimal_places=2)
    unit = models.CharField('单位', max_length=4, choices=UNIT_CHOICES)

    class Meta:
        verbose_name = '提货明细'
        verbose_name_plural = verbose_name


class SalesOrderPickUpCost(models.Model):
    order = models.ForeignKey('SalesOrderPickUp', related_name='cost', verbose_name='对应单号')
    item = models.CharField('项目', max_length=1, choices=SALES_ORDER_PICK_UP_COST)
    amount = models.DecimalField('金额', max_digits=5, decimal_places=0)
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '提货费用'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{}-{}'.format(self.get_item_display(), self.amount)
