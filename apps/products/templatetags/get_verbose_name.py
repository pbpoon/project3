# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/23 11:35'

from django import template

register = template.Library()


@register.simple_tag
def get_verbose_name(object):
    return object._meta.verbose_name
