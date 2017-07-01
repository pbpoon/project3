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
            'block_num': forms.TextInput(
                attrs={'size': '4', 'class': "block_info", 'list': "block_info", 'onchange': 'get_source(this.id)'}),
            # 'be_from': forms.Select(attrs={'size': '3'}),
            # 'destination': forms.Select(attrs={'size': '3'}),
            'quantity': forms.TextInput(attrs={'style': 'width:5em', 'min': '0', 'step': '1', 'type': 'number'}),
            'price': forms.TextInput(attrs={'size': '3'}),
            'amount': forms.TextInput(attrs={'size': '3'}),
            'date': forms.TextInput(attrs={'type': 'date'}),
        }

    def clean_destination(self):
        cd = self.cleaned_data
        block_num = cd['block_num']
        bf = cd['be_from']
        de = cd['destination']
        if bf and de:
            if bf == de:
                raise forms.ValidationError('编号{}起始地 与 目的地不能相同!')
        return de

    def clean_block_num(self):
        block_num = self.cleaned_data['block_num']
        block_num = Product.objects.get(block_num_id=block_num).block_num_id
        return block_num

    def clean(self):
        cd = self.cleaned_data
        print(cd)
        return cd

class KSOrderItemForm(forms.ModelForm):
    class Meta:
        model = KSOrderItem
        exclude = ('amount',)
        widgets = {
            # 'line_num': forms.TextInput(attrs={'size': '2'}),
            'block_num': forms.TextInput(
                attrs={'size': '4', 'class': "block_info", 'list': "block_info",
                       'onchange': 'get_source(this.id)'}),
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
            'block_num': forms.TextInput(
                attrs={'size': '4', 'class': "block_info", 'list': "block_info", 'onchange': 'get_source(this.id)'}),
            'quantity': forms.NumberInput(
                attrs={'style': 'width:5em', 'min': '0', 'type': 'number'}),
            'thickness': forms.NumberInput(attrs={'size': '2', 'type': 'number'}),
            'pic': forms.NumberInput(attrs={'size': '3', 'type': 'number'}),
            'price': forms.NumberInput(attrs={'size': '3', 'type': 'number'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cd = self.cleaned_data
        block_num = cd['block_num']
        ks_block_num_list = [item.block_num for item in KSOrderItem.objects.filter(order__status='N')]
        if block_num not in ks_block_num_list:
            raise forms.ValidationError('荒料编号{}#，没有介石记录请检查清楚'.format(block_num))
        return self.cleaned_data


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
