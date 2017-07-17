# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/23 11:35'

from django import template

register = template.Library()


@register.filter('verbose_name')
def verbose_name(value, arg):
    return value._meta.get_field(field_name=arg).verbose_name
    # return value._meta.verbose_name