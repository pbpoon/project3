from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.core.urlresolvers import reverse

SUPPLIER_TYPE_CHOICES = (('trade', '贸易公司'), ('quarry', '矿山'), ('shipping', '进口代理'))


class Supplier(models.Model):
    type = models.CharField('供应商类型', choices=SUPPLIER_TYPE_CHOICES, max_length=12)
    name = models.CharField('名称', max_length=20)
    address = models.CharField('地址', max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = '供应商资料'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('purchase:supplier', args=[self.id])


def file_get_upload_to(instance, filename):
    return '{0}/%Y%m%d/{1}'.format(instance.order, filename)


class OrderAbstract(models.Model):
    order = models.CharField('订单号', max_length=16, unique=True, db_index=True, default='new')
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry', verbose_name='数据录入人')
    handler = models.ForeignKey(User, related_name='%(class)s_handler', verbose_name='经办人')
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    file = models.FileField('相关文件', upload_to=file_get_upload_to, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-created']

    def __str__(self):
        return self.order

    def save(self, *args, **kwargs):
        # 格式为 IM1703001
        date_str = datetime.now().strftime('%y%m')
        if self.order == 'new':
            last_record = self.__class__.objects.last()
            if last_record:
                last_order = last_record.order
                if date_str in last_order[2:6]:
                    self.order = self.type + str(int(last_order[2:9]) + 1)
                else:
                    self.order = self.type + date_str + '001'  # 新月份
            else:
                self.order = self.type + date_str + '001'  # 新记录
        super(OrderAbstract, self).save(*args, **kwargs)


class PurchaseOrder(OrderAbstract):
    date = models.DateField('采购日期')
    type = models.CharField('订单类型', default='PC', max_length=2)
    supplier = models.ForeignKey('Supplier', related_name='sale_order', verbose_name='供应商')
    cost_money = models.CharField('结算货币', choices=(('USD', '$美元'), ('CNY', '￥人民币'), ('EUR', '€欧元')), default='USD',
                                  max_length=8)

    class Meta:
        verbose_name = '采购订单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order

    def get_absolute_url(self):
        return reverse('purchase:purchase_order', args=[self.id])

    def _get_total_count(self):
        return self.__class__.objects.filter(order=self.order).count()

    total_count = property(_get_total_count)

    def _get_total_weight(self):
        return sum(i.weight for i in self.item.all())

    total_weight = property(_get_total_weight)

    def _get_total_m3(self):
        return sum(i.m3 for i in self.item.all())

    total_m3 = property(_get_total_m3)


class PurchaseOrderItem(models.Model):
    order = models.ForeignKey('PurchaseOrder', related_name='item', verbose_name='采购订单')
    block_num = models.CharField('荒料编号', max_length=20, unique=True, db_index=True)
    price = models.DecimalField('单价', max_digits=9, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = '采购订单明细'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.block_num

    def _get_weight(self):
        return self.block.weight

    weight = property(_get_weight)

    def _get_m3(self):
        return self.block.m3

    m3 = property(_get_m3)


class ImportOrder(OrderAbstract):
    type = models.CharField('订单类型', default='IM', max_length=2)
    supplier = models.ForeignKey('Supplier', related_name='shipping_order', verbose_name='供应商',
                                 limit_choices_to={'type': 'shipping'})
    container = models.IntegerField('货柜数', null=True)
    price = models.DecimalField('单价', max_digits=9, decimal_places=2)
    order_date = models.DateField('下单日期', null=True, blank=True)

    class Meta:
        verbose_name = '进口代理订单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order


class ImportOrderItem(models.Model):
    order = models.ForeignKey('ImportOrder', related_name='item', verbose_name='进口代理订单')
    block_num = models.ForeignKey('products.Product', related_name='import_order', verbose_name='荒料编号')
    weight = models.DecimalField('重量', decimal_places=2, max_digits=9)

    class Meta:
        verbose_name = '进口代理单明细'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.block_num


def get_upload_to(instance, filename):
    return 'payment/{0}/%Y%m%d/{1}'.format(instance.order, filename)


USE_TYPE_CHOICES = (
    ('tt', 'TT'), ('lc', 'LC'), ('freight', '运费'), ('advance', '预付款'), ('kickback', '佣金'))


def payee_setdefault():
    return Supplier.objects.filter(name='delete')[0]


class PaymentHistory(models.Model):
    order = models.CharField('订单号', max_length=16)
    date = models.DateField('日期')
    amount = models.DecimalField('金额', max_digits=9, decimal_places=2)
    use_type = models.CharField('款项用途', choices=USE_TYPE_CHOICES, max_length=16)
    payee = models.ForeignKey('Supplier', on_delete=models.SET(payee_setdefault), verbose_name='收款人')
    payee_account = models.CharField('收款人账户', max_length=20)
    usd_amount = models.DecimalField('美金金额', max_digits=9, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField('汇率', max_digits=9, decimal_places=2, null=True, blank=True)
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    file = models.FileField('相关文件', upload_to=get_upload_to, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    data_entry_staff = models.ForeignKey(User, related_name='payment_entry', verbose_name='数据录入人')
    handler = models.ForeignKey(User, related_name='payment_handler', verbose_name='经办人')

    class Meta:
        verbose_name = '付款记录'
        verbose_name_plural = verbose_name
        ordering = ['-created']

    def __str__(self):
        return '[{0}]:{1}'.format(self.order, self.amount)
