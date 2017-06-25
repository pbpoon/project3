# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/24 13:42'

from django import forms


class PriceForm(forms.Form):
    price = forms.DecimalField()
