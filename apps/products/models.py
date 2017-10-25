from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from decimal import Decimal
from django.shortcuts import reverse
from process.models import ServiceProvider
from sales.models import SalesOrder

BLOCK_TYPE_CHOICES = (('block', '荒料'), ('coarse', '毛板'), ('slab', '板材'))
UNIT_CHOICES = (
    ('m3', 'm3'),
    ('ton', 'ton'),
)


class Product(models.Model):
    class Meta:
        verbose_name = '荒料信息'
        verbose_name_plural = verbose_name

    block_num = models.CharField('荒料编号', max_length=16, unique=True)
    weight = models.DecimalField('重量', max_digits=5, decimal_places=2, null=True)
    long = models.IntegerField('长', null=True)
    width = models.IntegerField('宽', null=True)
    high = models.IntegerField('高', null=True)
    m3 = models.DecimalField('立方', null=True, max_digits=5, decimal_places=2)
    category = models.ForeignKey('Category', verbose_name=u'品种名称')
    quarry = models.ForeignKey('Quarry', null=False, verbose_name=u'矿口')
    batch = models.ForeignKey('Batch', null=False, verbose_name=u'批次')
    updated = models.DateTimeField('更新日期', auto_now=True)
    created = models.DateTimeField('创建日期', auto_now_add=True)
    ps = models.CharField('备注信息', null=True, blank=True, max_length=200)

    # is_sell = models.BooleanField('是否已售', default=False)

    def _get_booking(self):
        if self.sale.exclude(order__status='C').exists():
            return True
        return False

    has_booking = property(_get_booking)

    def _get_sell(self):
        if self.sale.filter(order__status__in=('V', 'F')).exists():
            return True
        return False

    has_sell = property(_get_sell)

    def _get_cost_by(self):
        return self.purchase.order.cost_by

    cost_by = property(_get_cost_by)

    def _get_ccl(self):
        if self.slab.exists():
            cost_quantity = self.weight if self.cost_by == 'ton' else self.m3
            return '{:.2f}'.format(sum(slab.m2 for slab in self.slab.all()) / cost_quantity)
        return False

    ccl = property(_get_ccl)

    def __str__(self):
        return str(self.block_num)

    def get_absolute_url(self):
        return reverse('product:detail', args=[self.id])

    def get_slab_list(self, slab_ids=None, object_format=False, can_sell=False):
        obj = self.slab.all()

        if can_sell:
            obj = obj.filter(is_sell=False)
        if slab_ids:
            obj = obj.filter(id__in=slab_ids)
        slab_list = obj.values('block_num', 'thickness').annotate(
            block_pics=models.Count('id'),
            quantity=models.Sum('m2'))
        list = []

        for part in slab_list:
            part_list = [part for part in
                         obj.values('part_num').filter(
                             thickness=part['thickness']).distinct()]
            lst = {'block_num': self.block_num,
                   'thickness': str(part['thickness']),
                   'block_pics': str(part['block_pics']),
                   'quantity': str(part['quantity']),
                   'part_count': len(part_list),
                   'part_num': {},
                   'ids': [],
                   'unit': 'm2'}

            for item in part_list:
                slabs = [slab for slab in
                         obj.filter(thickness=part['thickness'],
                                    part_num=item['part_num']
                                    ).order_by('line_num')]
                part_num = item['part_num']
                lst['part_num'][part_num] = {}
                lst['part_num'][part_num]['part_pics'] = len(slabs)
                lst['part_num'][part_num]['part_m2'] = str(sum(slab.m2 for slab in slabs))
                lst['part_num'][part_num]['slabs'] = [s for s in slabs] if object_format \
                    else [s.id for s in slabs]
                lst['ids'].extend([s.id for s in slabs])
            list.append(lst)

        return list

    def get_block_list(self):
        cost_by = self.cost_by
        if cost_by == 'ton':
            quantity = {'quantity': self.weight, 'unit': cost_by}
        else:
            quantity = {'quantity': self.m3, 'unit': cost_by}
        lst = {'block_num': self.block_num, 'thickness': '荒料', 'block_pics': 1, 'part_count': 0,
               'ids': [self.block_num]}
        lst.update(quantity)
        return [lst]

    def get_inventory_list(self):
        block_type = self._get_block_type()
        cost_by = self.cost_by
        if cost_by == 'ton':
            inventory = {'quantity': self.weight, 'unit': cost_by}
        else:
            inventory = {'quantity': self.m3, 'unit': cost_by}

        if block_type == 'block':
            if self.sale.filter(order__status__in=('V', 'F')).exists():
                return [{'type': '已售', 'quantity': 0, 'unit': cost_by}]
            else:
                type = {'type': '荒料'}
                type.update(inventory)
                return [type]

        elif block_type == 'coarse':
            if cost_by == 'ton':
                quantity = '{:.0f}'.format(
                    100 / (float(self.ksorderitem_cost.thickness) + 0.35) / 2.8 * float(
                        self.weight))
            else:
                quantity = '{:.0f}'.format(
                    100 / (float(self.ksorderitem_cost.thickness) + 0.35) * float(self.m3))
            return [{'type': '毛板', 'quantity': quantity, 'unit': 'm2'}]

        elif block_type == 'slab':
            total_slab_pic = len(self.slab.all())
            total_coarse_pic = sum(i.pic + i.pi for i in self.ksorderitem_cost.all())
            thickness = min(i.thickness for i in self.ksorderitem_cost.all())
            balance_pic = total_slab_pic - total_coarse_pic
            quantity = '{:.2f}'.format(
                sum(item.m2 for item in self.slab.all() if not item._get_booking()))
            if not 0 < balance_pic > 8:
                return [{'type': '光板', 'quantity': quantity, 'unit': 'm2'}]
            if cost_by == 'ton':
                per_pic_m2 = '{:.0f}'.format(
                    100 / (float(thickness) + 0.35) / 2.8 * float(
                        self.weight) / sum(i.pic for i in self.ksorderitem_cost.all()))
            else:
                per_pic_m2 = '{:.0f}'.format(
                    100 / (float(thickness) + 0.35) * float(
                        self.m3) / sum(i.pic for i in self.ksorderitem_cost.all()))
            coarse_quantity = float(balance_pic) * float(per_pic_m2)
            return [{'type': '光板', 'quantity': quantity, 'unit': 'm2'},
                    {'type': '毛板', 'quantity': coarse_quantity, 'unit': 'm2'}]
        else:
            type = {'type': '运输中'}
            type.update(inventory)
            return [type]

    def _get_block_type(self):
        if self.mborderitem_cost.exists():
            return 'slab'
        elif self.ksorderitem_cost.exists():
            return 'coarse'
        elif self.storderitem_cost.exists():
            return 'block'
        else:
            return 'otw'  # on the way

    block_type = property(_get_block_type)

    def get_business(self):
        st_lst = [{'business': '荒料到货',
                   'quantity': item.quantity,
                   'unit': item.get_unit_display(),
                   'date': item.date,
                   'order': item.order,
                   'service_provider': item.order.service_provider,
                   'pic': ''}
                  for item in self.storderitem_cost.all()]

        ks_lst = [{'business': '界石',
                   'quantity': item.quantity,
                   'unit': item.get_unit_display(),
                   'date': item.date,
                   'order': item.order,
                   'service_provider': item.order.service_provider,
                   'pic': item.pic}
                  for item in self.ksorderitem_cost.all()]

        mb_lst = [{'business': '板材入库',
                   'quantity': item.quantity,
                   'unit': item.get_unit_display(),
                   'date': item.date,
                   'order': item.order,
                   'service_provider': item.order.service_provider,
                   'pic': item.pic}
                  for item in self.mborderitem_cost.all()]

        return sorted(st_lst + ks_lst + mb_lst, key=lambda k: k['date'])

    def get_salesorder(self):
        list = [{
                    'status': sale.order.get_status_display(),
                    'date': sale.order.date,
                    'part': sale.part,
                    'pic': sale.pic,
                    'quantity': sale.quantity,
                    'unit': sale.unit,
                    'price': sale.price,
                    'customer': sale.order.customer,
                    'order': sale.order
                } for sale in self.sale.all()]
        return sorted(list, key=lambda x: x['date'])

    def get_address(self):
        # if self._get_block_type == 'block':
        #     address = getattr(max([address for address in self.address.all() if address.type =='block'], key=lambda x: x.order.date),
        #         'address')
        # elif self._get_block_type == 'coarse':
        #     ks_pic = getattr(self.ksorderitem_cost.all()[0],'pic')
        #     all_coarse_ts_record=sorted([item for item in self.tsorderitem_cost.all() if item.block_type == 'coarse'], key=lambda x:x.date)
        #
        block_type = self._get_block_type()
        if self.address.exists():
            return getattr(max([address for address in self.address.filter(type=block_type)],
                               key=lambda x: x.order.date), 'address').name
        return '在途'
        # if last_record:
        #     if last_record =='slab':


class Slab(models.Model):
    block_num = models.ForeignKey('Product', on_delete=models.CASCADE,
                                  related_name='slab', verbose_name='荒料编号')
    thickness = models.DecimalField(max_digits=4, decimal_places=2,
                                    db_index=True, verbose_name=u'厚度')
    part_num = models.CharField(max_length=8, verbose_name=u'夹号')
    line_num = models.SmallIntegerField(u'序号')
    long = models.PositiveSmallIntegerField(verbose_name=u'长')
    high = models.PositiveSmallIntegerField(verbose_name=u'高')
    kl1 = models.PositiveSmallIntegerField(null=True, blank=True,
                                           verbose_name=u'长1')
    kl2 = models.PositiveSmallIntegerField(null=True, blank=True,
                                           verbose_name=u'长2')
    kh1 = models.PositiveSmallIntegerField(null=True, blank=True,
                                           verbose_name=u'高1')
    kh2 = models.PositiveSmallIntegerField(null=True, blank=True,
                                           verbose_name=u'高2')
    m2 = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                             verbose_name=u'平方')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'添加日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')
    address = models.ForeignKey('process.ServiceProvider', on_delete=models.SET_DEFAULT, default=1,
                                verbose_name='库存地址')
    is_sell = models.BooleanField(default=False, verbose_name=u'是否已售')
    is_booking = models.BooleanField(default=False, verbose_name=u'是否已定')
    is_pickup = models.BooleanField(default=False, verbose_name=u'是否已提货')

    #
    # def _get_sell(self):
    #     allows_status_sales_order_list = SalesOrder.objects.filter(status__in=('V', 'F')).all()
    #     all_slab_ids = ()
    #     if self.slab_list_items.filter(slablist__content_type__model='salesorder').exists():
    #         for sale in sales:
    #             if sale.order.status in ('V', 'F'):
    #                 return True
    #     else:
    #         return False
    # is_sell = property(_get_sell)
    #
    def _get_booking(self):
        if self.slab_list_items.filter(slablist__content_type__model='salesorder').exists():
            slablist = [slab.slablist for slab in self.slab_list_items.filter(
                slablist__content_type__model='salesorder').all()]
            for item in slablist:
                if item.order is None:
                    continue
                if item.order.status != 'C':
                    return True
        return False

    has_booking = property(_get_booking)

    #
    def _get_pickup(self):
        if self.slab_list_items.filter(slablist__content_type__model='salesorderpickup').exists():
            return True
        else:
            return False

    has_pickup = property(_get_pickup)

    class Meta:
        verbose_name = '码单'
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        k1 = 0
        k2 = 0
        if self.kl1 and self.kh1:
            k1 = (self.kl1 * self.kh1) / 10000
        if self.kl2 and self.kh2:
            k2 = (self.kl2 * self.kh2) / 10000
        m2 = (self.long * self.high) / 10000 - k1 - k2
        self.m2 = Decimal('{0:.2f}'.format(m2))
        super(Slab, self).save(*args, **kwargs)

    def __str__(self):
        k1 = ''
        k2 = ''
        if self.kh1 and self.kl1:
            k1 = '({0} x {1})'.format(self.kl1, self.kh1)
        if self.kh2 and self.kl2:
            k2 = '({0} x {1})'.format(self.kl2, self.kh2)
        return '{0} x {1} {2} {3} '.format(self.long, self.high, k1, k2)


class Batch(models.Model):
    name = models.CharField(max_length=20, unique=True, db_index=True,
                            verbose_name=u'批次编号')
    ps = models.CharField(max_length=200, null=True, blank=True,
                          verbose_name=u'备注信息')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField('更新日期', auto_now=True)

    class Meta:
        verbose_name = u'批次信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{0}票'.format(self.name)


class Category(models.Model):
    name = models.CharField(max_length=20, null=False, unique=True,
                            db_index=True, verbose_name=u'品种名称')
    created = models.DateField(auto_now_add=True, verbose_name=u'添加日期')

    class Meta:
        verbose_name = u'品种信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Quarry(models.Model):
    name = models.CharField(max_length=20, null=False, unique=True,
                            verbose_name=u'矿口名称')
    desc = models.CharField(max_length=200, verbose_name=u'描述信息')
    created = models.DateField(auto_now_add=True, verbose_name=u'添加日期')
    updated = models.DateField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        verbose_name = u'矿口信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


def get_address_default():
    defaule = {
        'service_type': 'OT',
        'name': 'DeleteDefault',
        'unit': 'x',
    }
    return ServiceProvider.objects.get_or_create(name='DeleteDefault', defaults=defaule)


class InventoryAddress(models.Model):
    block_num = models.ForeignKey('Product', on_delete=models.CASCADE,
                                  related_name='address', verbose_name='荒料编号')
    type = models.CharField('形态', max_length=6, choices=BLOCK_TYPE_CHOICES)
    address = models.ForeignKey('process.ServiceProvider',
                                on_delete=models.SET(get_address_default),
                                verbose_name='库存地址')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    order = GenericForeignKey()
    updated = models.DateTimeField('更新日期', auto_now=True)
    created = models.DateTimeField('创建日期', auto_now_add=True)

    class Meta:
        verbose_name = '库存地址'
        verbose_name_plural = verbose_name
        ordering = ('-updated',)

    def __str__(self):
        return '{}[{}]-{}'.format(self.block_num, self.type, self.address)

    @staticmethod
    def _save(order=None, block_num=None, address=None, block_type=None):
        _type = getattr(order, 'order_type')
        if _type == 'KS':
            type = 'coarse'
        elif _type == 'MB':
            type = 'slab'
        elif _type == 'ST':
            type = 'block'
        elif _type == 'TS':
            type = block_type
        else:
            type = InventoryAddress.objects.last().type
        if order and block_num and address and type:
            _address = InventoryAddress(order=order, block_num=block_num)
            _address.address = address
            _address.type = type
            _address.save()
            return True
        return False

#
# class Coarse(models.Model):
#     block_num = models.ForeignKey('Product', on_delete=models.CASCADE,
#                                      related_name='coarse', verbose_name='荒料编号')
#     address = models.ForeignKey('process.ServiceProvider', on_delete=models.SET_DEFAULT,default=1,
#                                 verbose_name='库存地址')
#     ks_order = models.OneToOneField()
#     quantity = models.DecimalField('数量', max_digits=5, decimal_places=2)
#     unit = models.CharField('单位', default='m2')
#     updated = models.DateTimeField('更新日期', auto_now=True)
#     created = models.DateTimeField('创建日期', auto_now_add=True)
#     is_del = models.BooleanField('删除', default=False)
#
#     class Meta:
#         verbose_name = '毛板库存数量'
#         verbose_name_plural = verbose_name
