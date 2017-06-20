# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/14 11:34'

from django import forms
from .models import ProcessOrder, TSOrderItem, MBOrderItem, KSOrderItem, STOrderItem
from products.models import Product


class ProcessOrderForm(forms.ModelForm):
    class Meta:
        model = ProcessOrder
        exclude = ()

def block_num_choice():
    return ((item.id, item.block_num) for item in Product.objects.values_list('id', 'block_num'))


class TSOrderItemForm(forms.ModelForm):
    class Meta:
        model = TSOrderItem
        fields = (
            'line_num', 'block_num', 'block_type', 'be_from', 'destination', 'quantity', 'unit', 'price', 'amount',
            'date',
            'ps')
        widgets = {
            'line_num': forms.TextInput(attrs={'size': '2'}),
            # 'block_num': forms.TextInput(attrs={'size': '3', 'list': 'block_list', 'v-on:click': 'get_list'}),
            # 'be_from': forms.Select(attrs={'size': '3'}),
            # 'destination': forms.Select(attrs={'size': '3'}),
            'quantity': forms.NumberInput(attrs={'size': '3', 'min': '0', 'step': '1'}),
            'unit': forms.TextInput(attrs={'size': '1'}),
            'price': forms.TextInput(attrs={'size': '3'}),
            'amount': forms.TextInput(attrs={'size': '3'}),
            'date': forms.DateInput(attrs={'size': '2', 'type': 'date'}),
        }


class KSOrderItemForm(forms.ModelForm):
    class Meta:
        model = KSOrderItem
        fields = '__all__'
        widgets = {
            'line_num': forms.TextInput(attrs={'size': '2'}),
            'block_num': forms.TextInput(attrs={'size': '3', 'list': 'block_num', 'v-on:click': 'get_list'}),
            'quantity': forms.NumberInput(attrs={'size': '2', 'min': '0', 'step': '1'}),
            'unit': forms.TextInput(attrs={'size': '1'}),
            'think': forms.TextInput(attrs={'size': '2'}),
            'pic': forms.TextInput(attrs={'size': '3'}),
            'pi': forms.TextInput(attrs={'size': '3'}),
            'price': forms.TextInput(attrs={'size': '3'}),
            'date': forms.DateInput(attrs={'size': '3', 'type': 'date'}),
        }


class MBOrderItemForm(forms.ModelForm):
    class Meta:
        model = MBOrderItem
        fields = '__all__'
        widgets = {
            'line_num': forms.TextInput(attrs={'size': '2'}),
            'block_num': forms.TextInput(attrs={'size': '3', 'list': 'block_num', 'v-on:click': 'get_list'}),
            'quantity': forms.NumberInput(attrs={'size': '2', 'min': '0', 'step': '1'}),
            'unit': forms.TextInput(attrs={'size': '1'}),
            'think': forms.TextInput(attrs={'size': '2'}),
            'pic': forms.TextInput(attrs={'size': '3'}),
            'price': forms.TextInput(attrs={'size': '3'}),
            'date': forms.DateInput(attrs={'size': '3', 'type': 'date'}),
        }


class STOrderItemForm(forms.ModelForm):
    class Meta:
        model = STOrderItem
        fields = '__all__'
        widgets = {
            'line_num': forms.TextInput(attrs={'size': '2'}),
            'block_num': forms.TextInput(attrs={'size': '3', 'list': 'block_num', 'v-on:click': 'get_list'}),
            'quantity': forms.NumberInput(attrs={'size': '2', 'min': '0', 'step': '1'}),
            'unit': forms.TextInput(attrs={'size': '1'}),
            'think': forms.TextInput(attrs={'size': '2'}),
            'price': forms.TextInput(attrs={'size': '3'}),
            'date': forms.DateInput(attrs={'size': '3', 'type': 'date'}),
        }
