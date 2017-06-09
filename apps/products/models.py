from django.db import models

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
