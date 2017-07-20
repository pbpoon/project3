# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/7/19 10:17'
from django import forms
from .models import SalesOrder, SalesOrderItem
from products.models import Product


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SalesOrderForm, self).__init__(*args, **kwargs)
        self.fields['city'].widget.attrs.update({'class': 'city'})
        self.fields['province'].widget.attrs.update({'class': 'province', 'onchange': 'choices_city()'})


class SalesOrderItemForm(forms.ModelForm):
    block_name = forms.CharField(label='荒料编号', widget=forms.TextInput(
        attrs={'size': '5', 'list': "block_info",
               'onchange': 'get_source(this.id)'}))

    class Meta:
        model = SalesOrderItem
        fields = '__all__'
        widgets = {
            'block_num': forms.HiddenInput()
        }

    def clean(self):
        cd = self.cleaned_data
        try:
            cd['block_num'] = Product.objects.get(block_num=cd['block_name'])
        except Exception as e:
            raise ValueError('荒料编号不在可销售范围！')
        return cd
