# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/14 11:34'

from django import forms
from .models import ProcessOrder, TSOrderItem, MBOrderItem, KSOrderItem, \
    STOrderItem, SlabList, SlabListItem
from products.models import Product, Slab
from products.forms import SlabForm
from crispy_forms.helper import FormHelper


class ProcessOrderForm(forms.ModelForm):
    class Meta:
        model = ProcessOrder
        exclude = ('order', 'line_num', 'status')
        widgets = {
            'date': forms.TextInput(attrs={'class': 'dt'}),
            'order_type': forms.HiddenInput(),
            'data_entry_staff': forms.HiddenInput(),
            'status': forms.TextInput(attrs={'readonly': True}),
        }

    def __init__(self, *args, **kwargs):
        super(ProcessOrderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()


def block_num_choice():
    return ((item.id, item.block_num) for item in
            Product.objects.values_list('id', 'block_num'))


WIDGETS_VALUES = {
    'block_num': forms.HiddenInput(),
    'quantity': forms.TextInput(
        attrs={'style': 'width:5em', 'min': '0'}),
    'price': forms.TextInput(attrs={'size': '3'}),
    'amount': forms.TextInput(attrs={'size': '3'}),
    'date': forms.TextInput(attrs={'class': 'dt', 'size': '6'}),
    'pic': forms.NumberInput(
        attrs={'style': 'width:5em', 'min': '0', 'step': '1',
               'type': 'number'}),
    'pi': forms.NumberInput(
        attrs={'style': 'width:5em', 'min': '0', 'step': '1',
               'type': 'number'}),
    'thickness': forms.NumberInput(attrs={'style': 'width:5em', 'min': '1.5'}),
}


class TSOrderItemForm(forms.ModelForm):
    block_name = forms.CharField(label='荒料编号', widget=forms.TextInput(
        attrs={'size': '5', 'list': "block_info",
               'onchange': 'get_source(this.id)'}))

    class Meta:
        model = TSOrderItem
        fields = ['block_name', 'be_from', 'block_type', 'destination',
                  'quantity', 'unit', 'price', 'date', 'ps']
        widgets = WIDGETS_VALUES

    def clean_destination(self):
        cd = self.cleaned_data
        block_num = cd.get('block_num', None)
        bf = cd['be_from']
        de = cd['destination']
        if bf and de:
            if bf == de:
                raise forms.ValidationError(
                    '编号{}起始地 与 目的地不能相同!'.format(block_num))
        return de

    def __init__(self, *args, **kwargs):
        super(TSOrderItemForm, self).__init__(*args, **kwargs)
        block_id = self.initial.get('block_num', None)
        self.empty_permitted = False
        """
        使用bootstrap的样色class
        """
        # for i in self.fields:
        #     attr_cls = self.fields[i].widget.attrs.get('class')
        #     if attr_cls:
        #         self.fields[i].widget.attrs['class'] += ' form-control'
        #     else:
        #         self.fields[i].widget.attrs.update({'class': 'form-control'})
        if block_id is not None:
            self.initial['block_name'] = Product.objects.get(
                id=block_id).block_num


class KSOrderItemForm(TSOrderItemForm):

    class Meta:
        model = KSOrderItem
        fields = '__all__'
        exclude = ('amount',)
        widgets = WIDGETS_VALUES

    def __init__(self, *args, **kwargs):
        super(KSOrderItemForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs.update({'readonly': True})
        self.fields['unit'].widget.attrs.update({'readonly': True})


class MBOrderItemForm(TSOrderItemForm):
    class Meta:
        model = MBOrderItem
        exclude = ('amount',)
        widgets = WIDGETS_VALUES

    def __init__(self, *args, **kwargs):
        super(MBOrderItemForm, self).__init__(*args, **kwargs)
        self.empty_permitted = False

    def clean_block_num(self):
        block_num = self.cleaned_data.get('block_num')
        ks_block_num_list = [item.block_num for item in
                             KSOrderItem.objects.filter(order__status='N')]
        if block_num not in ks_block_num_list:
            raise forms.ValidationError('荒料编号{}#，没有介石记录请检查清楚'.format(block_num))
        return block_num


class STOrderItemForm(forms.ModelForm):
    class Meta:
        model = STOrderItem
        exclude = ('amount',)
        widgets = WIDGETS_VALUES


class SlabListForm(forms.ModelForm):
    class Meta:
        model = SlabList
        exclude = ()


class SlabListItemForm(forms.ModelForm):
    # block_num = forms.CharField(max_length=16, label='荒料编号')
    # thickness = forms.DecimalField(max_digits=4, decimal_places=2, label='厚度')
    # part_num = forms.CharField(label='夹号')

    class Meta:
        model = SlabListItem
        exclude = ()


class CustomBaseInlineFormset(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(CustomBaseInlineFormset, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

    def clean(self):
        # if any(self.errors):
        #     return
        block_list = []
        for form in self.forms:
            if form.cleaned_data.get('block_num'):
                block_num = form.cleaned_data['block_num']
                if block_num in block_list:
                    raise forms.ValidationError(
                        '荒料编号[{}]有重复数据'.format(block_num))
                block_list.append(block_num)
                # super(CustomBaseInlineFormset, self).clean()
