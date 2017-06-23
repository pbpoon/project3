from django.db import models
from decimal import Decimal
from django.shortcuts import reverse

BLOCK_TYPE_CHOICES = (('block', '荒料'), ('coarse', '毛板'), ('slab', '板材'))


class Product(models.Model):
    block_num = models.OneToOneField('purchase.PurchaseOrderItem', to_field='block_num', db_constraint=False,
                                     related_name='block',
                                     verbose_name='荒料编号')
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
    price = models.DecimalField('单价', max_digits=9, decimal_places=2)
    ps = models.CharField('备注信息', null=True, blank=True, max_length=200)

    class Meta:
        verbose_name = '荒料信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.block_num)

    def get_absolute_url(self):
        return reverse('product:detail', args=[self.id])

    def get_slab_list(self):
        slab_list = self.slab.values('thickness').annotate(total_pics=models.Count('id'), total_m2=models.Sum('m2'))
        for part in slab_list:
            part['part_num'] = {}
            part_list = [part for part in
                         self.slab.values('part_num').filter(thickness=part['thickness']).distinct()]
            for item in part_list:
                slabs = [slab for slab in
                         self.slab.filter(thickness=part['thickness'],
                                          part_num=item['part_num']).order_by('line_num')]
                part['part_num'][item['part_num']] = {}
                part['part_num'][item['part_num']]['pics'] = len(slabs)
                part['part_num'][item['part_num']]['m2'] = sum(s.m2 for s in slabs)
                part['part_num'][item['part_num']]['slabs'] = slabs
        return slab_list


class Slab(models.Model):
    block_num = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='slab', verbose_name='荒料编号')
    thickness = models.DecimalField(max_digits=4, decimal_places=2, db_index=True, verbose_name=u'厚度')
    part_num = models.CharField(max_length=8, verbose_name=u'夹号')
    line_num = models.SmallIntegerField(u'序号')
    long = models.PositiveSmallIntegerField(verbose_name=u'长')
    high = models.PositiveSmallIntegerField(verbose_name=u'高')
    kl1 = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'长1')
    kl2 = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'长2')
    kh1 = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'高1')
    kh2 = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=u'高2')
    m2 = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=u'平方')
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
        return '{0} x {1} {2} {3} = {4}'.format(self.long, self.high, k1, k2, self.m2)


class Batch(models.Model):
    name = models.CharField(max_length=20, unique=True, db_index=True, verbose_name=u'批次编号')
    ps = models.CharField(max_length=200, null=True, blank=True, verbose_name=u'备注信息')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField('更新日期', auto_now=True)

    class Meta:
        verbose_name = u'批次信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{0}票'.format(self.name)


class Category(models.Model):
    name = models.CharField(max_length=20, null=False, unique=True, db_index=True, verbose_name=u'品种名称')
    created = models.DateField(auto_now_add=True, verbose_name=u'添加日期')

    class Meta:
        verbose_name = u'品种信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Quarry(models.Model):
    name = models.CharField(max_length=20, null=False, unique=True, verbose_name=u'矿口名称')
    desc = models.CharField(max_length=200, verbose_name=u'描述信息')
    created = models.DateField(auto_now_add=True, verbose_name=u'添加日期')
    updated = models.DateField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        verbose_name = u'矿口信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
