from django.db import models
from decimal import Decimal
from django.shortcuts import reverse

BLOCK_TYPE_CHOICES = (('block', '荒料'), ('coarse', '毛板'), ('slab', '板材'))


class Product(models.Model):
    block_num = models.CharField('荒料编号', max_length=16, unique=True)
    weight = models.DecimalField('重量', max_digits=5, decimal_places=2,
                                 null=True)
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

    # is_del = models.BooleanField('删除', default=False)

    class Meta:
        verbose_name = '荒料信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.block_num)

    def get_absolute_url(self):
        return reverse('product:detail', args=[self.id])

    def get_slab_list(self, slab_ids=None, object_format=False):
        obj = self.slab.all()
        if slab_ids:
            obj = obj.filter(id__in=slab_ids)
        slab_list = obj.values('block_num', 'thickness').annotate(
            block_pics=models.Count('id'),
            block_m2=models.Sum('m2'))
        list = []

        for part in slab_list:
            part_list = [part for part in
                         obj.values('part_num').filter(
                             thickness=part['thickness']).distinct()]
            lst = {}
            lst = {'block_num': self.block_num_id,
                   'thickness': str(part['thickness']),
                   'block_pics': str(part['block_pics']),
                   'block_m2': str(part['block_m2']),
                   'part_count': len(part_list), 'part_num': {}}

            for item in part_list:
                slabs = [slab for slab in
                         obj.filter(thickness=part['thickness'],
                                    part_num=item['part_num']).order_by(
                             'line_num')]
                part_num = item['part_num']
                lst['part_num'][part_num] = {}
                lst['part_num'][part_num]['part_pics'] = len(slabs)
                lst['part_num'][part_num]['part_m2'] = str(
                    sum(s.m2 for s in slabs))
                slab = [s.id for s in slabs]
                if object_format:
                    slab = [s for s in slabs]
                lst['part_num'][part_num]['slabs'] = slab
            list.append(lst)

        return list

    def _get_cost_by(self):
        return self.purchase.order.cost_by
    cost_by = property(_get_cost_by)

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
    is_sell = models.BooleanField(default=False, verbose_name=u'是否已售')
    is_booking = models.BooleanField(default=False, verbose_name=u'是否已定')
    is_pickup = models.BooleanField(default=False, verbose_name=u'是否已提货')

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

    '''
    注释的代码为返回码单为字典类型
    '''

    # def get_slab_list(self, slab_ids=None, object_format=False):
    #     obj = self.slab.all()
    #     if slab_ids:
    #         obj = self.slab.filter(id__in=slab_ids)
    #     slab_list = obj.values('block_num', 'thickness').annotate(block_pics=models.Count('id'),
    #                                                               block_m2=models.Sum('m2'))
    #     lst = {}
    #     lst[self.block_num_id] = {}
    #     # lst[self.block_num_id]['block_num'] = self.block_num_id
    #     for part in slab_list:
    #         lst[self.block_num_id][part['thickness']] = {'block_pics': part['block_pics'],
    #                                                      'block_m2': part['block_m2'], 'part_num': {}}
    #         part_list = [part for part in
    #                      obj.values('part_num').filter(thickness=part['thickness']).distinct()]
    #         for item in part_list:
    #             slabs = [slab for slab in
    #                      obj.filter(thickness=part['thickness'],
    #                                 part_num=item['part_num']).order_by('line_num')]
    #             part_num = item['part_num']
    #             # lst[self.block_num_id][part['thickness']]['part_num'] = {}
    #             lst[self.block_num_id][part['thickness']]['part_num'][part_num] = {}
    #             lst[self.block_num_id][part['thickness']]['part_num'][part_num]['part_pics'] = len(slabs)
    #             lst[self.block_num_id][part['thickness']]['part_num'][part_num]['part_m2'] = sum(s.m2 for s in slabs)
    #             slab = [s.id for s in slabs]
    #             if object_format:
    #                 slab = [s for s in slabs]
    #             lst[self.block_num_id][part['thickness']]['part_num'][part_num]['slabs'] = slab
    #     return lst
