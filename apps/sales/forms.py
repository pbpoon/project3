# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/7/19 10:17'
from django import forms
from .models import SalesOrder, SalesOrderItem, CustomerInfo
from products.models import Product


class CustomerInfoForm(forms.ModelForm):
    class Meta:
        model = CustomerInfo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CustomerInfoForm, self).__init__(*args, **kwargs)
        self.fields['city'].widget.attrs.update({'class': 'city'})
        self.fields['province'].widget.attrs.update(
            {'class': 'province', 'onchange': 'choices_city()'})


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SalesOrderForm, self).__init__(*args, **kwargs)
        self.fields['city'].widget.attrs.update({'class': 'city'})
        self.fields['province'].widget.attrs.update(
            {'class': 'province', 'onchange': 'choices_city()'})


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

    def __init__(self, *args, **kwargs):
        super(SalesOrderItemForm, self).__init__(*args, **kwargs)
        block_id = self.initial.get('block_num', None)
        if block_id:
            self.initial['block_name'] = Product.objects.get(id=block_id).block_num


    def clean(self):
        cd = self.cleaned_data
        if Product.objects.filter(block_num=cd['block_name']).exists():
            raise ValueError('荒料编号不在可销售范围！')
        return cd
