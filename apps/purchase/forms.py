# _*_ conding:utf-8 _*_
__author__ = 'pbpoon'
__date__ = '2017/6/4 22:37'

from django import forms
from .models import PurchaseOrderItem, PurchaseOrder, ImportOrder, PaymentHistory
from products.models import Product, Batch


class ImportOrderForm(forms.ModelForm):
    class Meta:
        model = ImportOrder
        fields = ['finish_pay', 'supplier', 'order_date', 'container', 'price', 'handler', 'ps', 'file']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['finish_pay', 'handler', 'date', 'supplier', 'cost_money', 'cost_by', 'ps', 'file']


COST_TYPE_CHOICES = (('ton', '按重量'), ('m3', '按立方'))


class PurchaseOrderItemForm(forms.ModelForm):
    weight = forms.DecimalField(label='重量', max_digits=9, decimal_places=2, help_text='单位为：吨', required=False)
    long = forms.IntegerField(label='长', help_text='单位：厘米', required=False)
    width = forms.IntegerField(label='宽', help_text='单位：厘米', required=False)
    high = forms.IntegerField(label='高', help_text='单位：厘米', required=False)
    m3 = forms.DecimalField(label='立方', max_digits=9, decimal_places=2, help_text='单位为：立方米', required=False)
    batch = forms.ChoiceField(label='批次')
    ps = forms.CharField(label='备注信息', required=False)

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # super(self.__class__, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            initial = kwargs.setdefault('initial', {})
            initial['batch'] = [(x.id, x.name) for x in Batch.objects.all()]
        forms.ModelForm.__init__(self, *args, **kwargs)

    def clean_block_num(self):
        block_num = self.cleaned_data['block_num']
        bk = Product.objects.get(block_num=block_num)
        return bk

    def clean(self):
        cd = self.cleaned_data
        if cd['cost_type'] == 1:
            if cd['weight'] is None or cd['weight'] <= 0:
                raise forms.ValidationError('重量不能为空或为零')
        return self.cleaned_data

    def save(self, commit=True):
        block_num = self.save(commit=False)
        cd = forms.ModelForm.cleaned_data
        if cd['cost_type'] == 'ton':
            cd['m3'] = (cd['long'] * cd['width'] * cd['high']) / 100000
        cd['batch'] = Batch.objects.filter(name=cd['batch'])[0]
        if commit:
            block_num.save()
            Product.objects.create(block_num=block_num, weight=cd['weight'], long=cd['long'], width=cd['width'],
                                   high=cd['high'], m3=cd['m3'], batch=cd['batch'], cost_type=cd['cost_type'],
                                   ps=cd['ps'])
        return block_num


def get_choices_list():
    purchase_order = [(i.order, i.order + '[采购]') for i in PurchaseOrder.objects.filter(finish_pay=False)]
    import_order = [(i.order, i.order + '[运输]') for i in ImportOrder.objects.filter(finish_pay=False)]
    return purchase_order + import_order


class PaymentForm(forms.ModelForm):
    class Meta:
        model = PaymentHistory
        exclude = ['data_entry_staff']

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['order'] = forms.ChoiceField(label='相关订单号', widget=forms.Select, required=False,
                                                 choices=get_choices_list())


class CustomBaseInlineFormset(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(CustomBaseInlineFormset, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

    def clean(self):
        block_list = []
        for form in self.forms:
            if form.cleaned_data.get('block_num'):
                block_num = form.cleaned_data['block_num']
                if block_num in block_list:
                    raise forms.ValidationError('荒料编号[{}]有重复数据'.format(block_num))
                block_list.append(block_num)

