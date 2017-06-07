# _*_ conding:utf-8 _*_
__author__ = 'pbpoon'
__date__ = '2017/6/7 22:06'

from .models import PurchaseOrder, PurchaseOrderItem, ImportOrder, ImportOrderItem
from import_export import resources


class ImportOrderItemResources(resources.ModelResource):
    class Meta:
        model = ImportOrderItem
