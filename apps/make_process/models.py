from django.db import models

BLOCK_TYPE_CHOICES = (
    ('block', '荒料'),
    ('coarse', '毛板'),
    ('slab', '板材')
)
PROCESS_STATUS_CHOICES = (
    ('block', '海运'),
    ('coarse', '运输'),
    ('slab', '补板')
)


class ProcessStatus(models.Model):
    status = models.CharField(choices=PROCESS_STATUS_CHOICES)
    block_num = models.ForeignKey('products.Product', on_delete=models.CASCADE, verbose_name='荒料编号')
    type = models.CharField('形态', choices=BLOCK_TYPE_CHOICES, max_length=6, default='block')

