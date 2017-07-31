from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, \
    GenericRelation
from django.contrib.auth.models import User
from django.shortcuts import reverse
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist

BLOCK_TYPE_CHOICES = (
    ('block', '荒料'),
    ('coarse', '毛板'),
    ('slab', '板材')
)
SERVICE_TYPE_CHOICES = (
    ('TS', '运输'),
    ('MB', '补板'),
    ('KS', '界石'),
)
ORDER_TYPE_CHOICES = (
    ('TS', '运输单'),
    ('MB', '补板单'),
    ('KS', '界石单'),
    ('ST', '荒料入库单')
)
STATUS_CHOICES = (
    ('N', '新订单'),
    ('V', '核实'),
    ('F', '完成'),
    ('C', '关闭'),
    ('M', '修改过')
)

UNIT_CHOICES = (
    ('m2', 'm2'),
    ('m3', 'm3'),
    ('che', '车'),
    ('ton', 'ton'),
)


class ServiceProvider(models.Model):
    name = models.CharField('名称', max_length=80, unique=True, db_index=True)
    service_type = models.CharField('服务类型', max_length=2,
                                    choices=SERVICE_TYPE_CHOICES)
    default_price = models.DecimalField('默认单价', max_digits=9, decimal_places=2,
                                        default=0)
    unit = models.CharField('单位', max_length=4, choices=UNIT_CHOICES)
    address = models.CharField('地址', max_length=100, null=True, blank=True)
    desc = models.CharField('补充说明', max_length=200, null=True, blank=True)
    contacts = models.CharField('联系人', max_length=8, null=True, blank=True)
    telephone = models.CharField('联系电话', max_length=11, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '服务商信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '[{0}]{1}'.format(self.get_service_type_display(), self.name)

    def get_absolute_url(self):
        return reverse('process:serviceprovider_detail', args=[self.id])


class ProcessOrder(models.Model):
    status = models.CharField('订单状态', max_length=1, choices=STATUS_CHOICES,
                              default='N')
    order_type = models.CharField('订单类型', max_length=2,
                                  choices=ORDER_TYPE_CHOICES)
    order = models.CharField('订单号', max_length=16, unique=True, db_index=True,
                             default='new')
    date = models.DateField('订单日期', db_index=True)
    service_provider = models.ForeignKey('ServiceProvider', verbose_name='服务商')
    service_provider_order = models.CharField('对方单号', null=True, blank=True,
                                              max_length=20)
    handler = models.ForeignKey(User, related_name='%(class)s_handler',
                                verbose_name='经办人')
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry',
                                         verbose_name='数据录入人')
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)
    slab_list = GenericRelation('SlabList')

    class Meta:
        verbose_name = '加工订单'
        verbose_name_plural = verbose_name
        ordering = ['-updated']

    def get_absolute_url(self):
        return reverse('process:order_detail', args=[self.id])

    def __str__(self):
        return '[{0}]{1}'.format(self.get_order_type_display(), self.order)

    def save(self, *args, **kwargs):
        # 格式为 IM1703001
        service_type = self.order_type
        date_str = datetime.now().strftime('%y%m')
        if self.order == 'new':
            try:
                last_order = max([item.order for item in
                                  ProcessOrder.objects.filter(
                                      order_type=service_type)])
                if date_str in last_order[2:6]:
                    value = service_type + str(int(last_order[2:9]) + 1)
                else:
                    value = service_type + date_str + '001'  # 新月份
            except Exception as e:
                value = service_type + date_str + '001'  # 新记录
            finally:
                self.status = 'N'
                self.order = value
        super(ProcessOrder, self).save(*args, **kwargs)

    def get_total_amount(self):
        order_type = self.order_type
        model_name = '{0}OrderItem'.format(order_type[:1].upper())
        total_amount = sum(
            item.amount for item in model_name.objects.filter(order=self.id))
        return Decimal('{0:.2f}'.format(total_amount))

    total_amount = property(get_total_amount)


class OrderItemBaseModel(models.Model):
    order = models.ForeignKey('ProcessOrder', related_name='%(class)s',
                              verbose_name='加工订单号')
    line_num = models.SmallIntegerField('序号', null=True, blank=True)
    block_num = models.ForeignKey('products.Product', on_delete=models.CASCADE,
                                  related_name='%(class)s_cost',
                                  verbose_name='荒料编号')
    quantity = models.DecimalField('数量', max_digits=6, decimal_places=2)
    unit = models.CharField('单位', max_length=4, choices=UNIT_CHOICES)
    price = models.DecimalField('价格', max_digits=9, decimal_places=2)
    amount = models.DecimalField('金额', decimal_places=2, max_digits=6,
                                 null=True, blank=True)
    date = models.DateField('日期')
    ps = models.CharField('备注信息', max_length=100, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['line_num']

    def get_amount(self):
        amount = self.quantity * self.price
        return Decimal('{0:.2f}'.format(amount))

    def save(self, *args, **kwargs):
        if not self.line_num:
            self.line_num = self.__class__.objects.filter(
                order=self.order).count()
        if not self.unit:
            self.unit = self.get_unit()
        self.amount = self.get_amount()
        super(OrderItemBaseModel, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.block_num)


class TSOrderItem(OrderItemBaseModel):
    block_type = models.CharField('形态', choices=BLOCK_TYPE_CHOICES,
                                  max_length=6)
    be_from = models.ForeignKey('ServiceProvider', verbose_name='起始地',
                                related_name='TS_from')
    destination = models.ForeignKey('ServiceProvider', related_name='TS_to',
                                    verbose_name='目的')
    slab_list = GenericRelation('SlabList')

    class Meta:
        verbose_name = '运输单'
        verbose_name_plural = verbose_name

    def get_unit(self):
        return 'che'


class MBOrderItem(OrderItemBaseModel):
    thickness = models.DecimalField('厚度', max_digits=4, decimal_places=2)
    pic = models.SmallIntegerField('件数', null=True, blank=True)

    class Meta:
        verbose_name = '补板加工单'
        verbose_name_plural = verbose_name

    def get_unit(self):
        return 'm2'


class KSOrderItem(OrderItemBaseModel):
    thickness = models.DecimalField('厚度', max_digits=4, decimal_places=2)
    pic = models.SmallIntegerField('件数', null=True, blank=True)
    pi = models.SmallIntegerField('板皮', null=True, blank=True)

    class Meta:
        verbose_name = '界石加工单'
        verbose_name_plural = verbose_name

    def get_amount(self):
        cost_by = self.block_num.cost_by
        if cost_by == 'ton':
            amount = Decimal(self.quantity) / Decimal(2.8) * Decimal(self.price)
        else:
            amount = Decimal(self.quantity) / Decimal(self.price)
        return Decimal('{0:.2f}'.format(amount))

    def get_unit(self):
        return 'm3'


class STOrderItem(OrderItemBaseModel):
    def get_amount(self):
        return Decimal('{0:.2f}'.format(self.amount))

    class Meta:
        verbose_name = '荒料到货单'
        verbose_name_plural = verbose_name


class SlabList(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    order = GenericForeignKey()
    data_entry_staff = models.ForeignKey(User, related_name='date_entry',
                                         verbose_name='数据录入人')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'添加日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        verbose_name = u'码单信息'
        verbose_name_plural = verbose_name
        ordering = ['-updated']

    def __str__(self):
        return str(self.order)

    @property
    def total(self):
        part = len(self.item.distinct('part_num'))
        pic = len(self.item.all())
        m2 = sum(item.m2 for item in self.item.all())
        return {'part': part, 'pic': pic, 'm2': Decimal('{0:.2f}'.format(m2))}

    @property
    def can_sell(self):
        part = len(self.item.filter(is_booking=False, is_sell=False).distinct(
            'part_num'))
        pic = len(self.item.filter(is_booking=False, is_sell=False))
        m2 = sum(item.m2 for item in
                 self.item.filter(is_booking=False, is_sell=False))
        return {'part': part, 'pic': pic, 'm2': Decimal('{0:.2f}'.format(m2))}

    @property
    def can_pickup(self):
        part = len(self.item.filter(is_pickup=False).distinct('part_num'))
        pic = len(self.item.filter(is_pickup=False))
        m2 = sum(item.m2 for item in self.item.filter(is_pickup=False))
        return {'part': part, 'pic': pic, 'm2': Decimal('{0:.2f}'.format(m2))}


class SlabListItem(models.Model):
    slablist = models.ForeignKey('SlabList', related_name='item',
                             verbose_name=u'对应码单')
    part_num = models.CharField(max_length=8, verbose_name=u'夹号')
    line_num = models.SmallIntegerField(u'序号', blank=True, null=True)
    slab = models.ForeignKey('products.Slab', on_delete=models.CASCADE,
                             verbose_name='板材编号')

    def __str__(self):
        return str(self.slab)

    def _get_m2(self):
        return self.slab.m2

    m2 = property(_get_m2)
