from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from datetime import datetime

BLOCK_TYPE_CHOICES = (
    ('block', '荒料'),
    ('coarse', '毛板'),
    ('slab', '板材')
)
SERVICE_TYPE_CHOICES = (
    ('TS', '运输'),
    ('MB', '补板'),
    ('KS', '界石')
)


class ServiceProvider(models.Model):
    name = models.CharField('名称', max_length=80, unique=True, db_index=True)
    service_type = models.CharField('服务类型', max_length=2, choices=SERVICE_TYPE_CHOICES)
    default_price = models.DecimalField('默认单价', max_digits=9, decimal_places=2, default=0)
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
        return '[{}]{}'.format(self.service_type, self.name)


class OrderBaseModel(models.Model):
    order = models.CharField('订单号', max_length=16, unique=True, db_index=True, default='new')
    date = models.DateField('订单日期', db_index=True)
    service_provider = models.ForeignKey('ServiceProvider', verbose_name='服务商')
    service_provider_order = models.CharField('对方单号', null=True, blank=True, max_length=20)
    handler = models.ForeignKey(User, related_name='%(class)s_handler', verbose_name='经办人')
    data_entry_staff = models.ForeignKey(User, related_name='%(class)s_entry', verbose_name='数据录入人')
    ps = models.CharField('备注信息', max_length=200, null=True, blank=True)
    created = models.DateField('创建日期', auto_now_add=True)
    updated = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        abstract = True

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
        super(OrderBaseModel, self).save(*args, **kwargs)


class ProcessStatus(models.Model):
    status = models.CharField(choices=PROCESS_STATUS_CHOICES)
    block_num = models.ForeignKey('products.Product', on_delete=models.CASCADE, verbose_name='荒料编号')
    type = models.CharField('形态', choices=BLOCK_TYPE_CHOICES, max_length=6, default='block')
