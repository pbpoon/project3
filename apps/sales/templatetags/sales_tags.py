# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/8/11 17:24'
from django import template
from ..models import SalesOrder

register = template.Library()


@register.inclusion_tag('sales/about_this_order.html', takes_context=True)
def about_this_order(context, order_id=None):
    request = context['request']
    order = SalesOrder.objects.get(pk=order_id)
    goback = False if request.path == order.get_absolute_url() else True
    return {'order': order, 'goback': goback}
