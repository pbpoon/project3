# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/14 11:34'

from django import forms
from .models import ProcessOrder, TSOrderItem, MBOrderItem, KSOrderItem, STOrderItem, SlabList
from products.models import Product, Slab


class ProcessOrderForm(forms.ModelForm):
    class Meta:
        model = ProcessOrder
        exclude = ('data_entry_staff', 'order', 'line_num')
        widgets = {
            'date': forms.TextInput(attrs={'type': 'date'}),
            'order_type': forms.HiddenInput()
        }


def block_num_choice():
    return ((item.id, item.block_num) for item in Product.objects.values_list('id', 'block_num'))


class TSOrderItemForm(forms.ModelForm):
    class Meta:
        model = TSOrderItem
        exclude = ('amount', 'order')
        widgets = {
            # 'line_num': forms.TextInput(attrs={'size': '2'}),
            # 'block_num': forms.TextInput(attrs={'size': '3', 'list': 'block_list', 'v-on:click': 'get_list'}),
            # 'be_from': forms.Select(attrs={'size': '3'}),
            # 'destination': forms.Select(attrs={'size': '3'}),
            'quantity': forms.TextInput(attrs={'style': 'width:5em', 'min': '0', 'step': '1', 'type': 'number'}),
            'price': forms.TextInput(attrs={'size': '3'}),
            'amount': forms.TextInput(attrs={'size': '3'}),
            'date': forms.TextInput(attrs={'type': 'date'}),
        }


class KSOrderItemForm(forms.ModelForm):
    class Meta:
        model = KSOrderItem
        exclude = ('amount',)
        widgets = {
            # 'line_num': forms.TextInput(attrs={'size': '2'}),
            # 'block_num': forms.TextInput(attrs={'size': '3', 'list': 'block_num', 'v-on:click': 'get_list'}),
            'quantity': forms.NumberInput(attrs={'style': 'width:5em', 'min': '0', 'type': 'number'}),
            'thickness': forms.NumberInput(attrs={'size': '2', 'min': '0', 'type': 'number'}),
            'pic': forms.NumberInput(attrs={'size': '3', 'min': '0', 'step': '1', 'type': 'number'}),
            'pi': forms.NumberInput(attrs={'size': '3', 'min': '0', 'step': '1', 'type': 'number'}),
            'price': forms.NumberInput(attrs={'size': '3'}),
            'date': forms.TextInput(attrs={'type': 'date'}),
        }


class MBOrderItemForm(forms.ModelForm):
    class Meta:
        model = MBOrderItem
        exclude = ('amount',)
        widgets = {
            # 'line_num': forms.TextInput(attrs={'size': '2'}),
            # 'block_num': forms.ChoiceWidget(attrs={'size': '3', 'disabled': 'disabled'}),
            'quantity': forms.TextInput(
                attrs={'style': 'width:5em', 'min': '0', 'step': '1', 'type': 'number', 'disabled': 'disabled'}),
            'thickness': forms.TextInput(attrs={'size': '2', 'disabled': 'disabled'}),
            'pic': forms.TextInput(attrs={'size': '3', 'disabled': 'disabled'}),
            'price': forms.TextInput(attrs={'size': '3'}),
            'date': forms.TextInput(attrs={'type': 'date'}),
        }


class STOrderItemForm(forms.ModelForm):
    class Meta:
        model = STOrderItem
        exclude = ('amount',)
        widgets = {
            # 'line_num': forms.TextInput(attrs={'size': '2'}),
            'block_num': forms.TextInput(attrs={'size': '3', 'list': 'block_num', 'v-on:click': 'get_list'}),
            'quantity': forms.TextInput(attrs={'style': 'width:5em', 'min': '0', 'step': '1', 'type': 'number'}),
            'unit': forms.TextInput(attrs={'size': '1'}),
            'think': forms.TextInput(attrs={'size': '2'}),
            'price': forms.TextInput(attrs={'size': '3'}),
            'date': forms.TextInput(attrs={'size': '2', 'type': 'date'}),
        }


class SlabListForm(forms.ModelForm):
    class Meta:
        model = SlabList
        exclude = ()


class SlabListItemForm(forms.ModelForm):
    class Meta:
        model = Slab
        exclude = ('block_num', 'thickness', 'created', 'updated', 'is_booking', 'is_pickup', 'is_sell', 'm2')


class CustomBaseInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        block_list = []
        for form in self.forms:
            block_num = form.cleaned_data['block_num']
            if block_num in block_list:
                raise forms.ValidationError('荒料编号不能重复')
            block_list.append(block_num)
