# _*_ conding:utf-8 _*_
__author__ = 'pbpoon'
__date__ = '2017/6/4 22:33'

from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['block_num', 'weight', 'long', 'width', 'high', 'm3', 'batch', 'cost_type', 'ps']
