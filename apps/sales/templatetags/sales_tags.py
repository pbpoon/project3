# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/8/11 17:24'
from django import template
from ..models import SalesOrder

register = template.Library()


@register.inclusion_tag('sales/about_this_order.html')
def about_this_order(order_id=None):
    return {'order': SalesOrder.objects.get(pk=order_id)}
