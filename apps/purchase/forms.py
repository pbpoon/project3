# _*_ conding:utf-8 _*_
__author__ = 'pbpoon'
__date__ = '2017/6/4 22:37'

from django import forms
from .models import PurchaseOrderItem, PurchaseOrder, ImportOrderItem, ImportOrder
from products.models import Product, Batch
from djangoformsetjs.utils import formset_media_js


class ImportOrdetItemForm(forms.ModelForm):
    class Meta:
        model = ImportOrderItem
        fields = '__all__'
        widgets = {
            'block_num': forms.TextInput(attrs={'size': '10'})
        }

    class MyForm(forms.Form):
        class Media(object):
            js = formset_media_js + (
                # Other form media here
            )


class ImportOrderForm(forms.ModelForm):
    class Meta:
        model = ImportOrder
        fields = ['supplier', 'order_date', 'container', 'price', 'handler', 'ps', 'file']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['handler', 'date', 'supplier', 'cost_money', 'cost_by', 'ps', 'file']


class AddExcelForm(forms.Form):
    file = forms.FileField(label='上传文件')


COST_TYPE_CHOICES = (('1', '按重量'), ('2', '按立方'))


class PurchaseOrderItemForm(forms.ModelForm):
    weight = forms.DecimalField(label='重量', max_digits=9, decimal_places=2, help_text='单位为：吨', required=False)
    long = forms.IntegerField(label='长', help_text='单位：厘米', required=False)
    width = forms.IntegerField(label='宽', help_text='单位：厘米', required=False)
    high = forms.IntegerField(label='高', help_text='单位：厘米', required=False)
    m3 = forms.DecimalField(label='立方', max_digits=9, decimal_places=2, help_text='单位为：立方米', required=False)
    batch = forms.ChoiceField(label='批次')
    cost_type = forms.ChoiceField(label='成本计算方式', choices=COST_TYPE_CHOICES)
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

    def clean(self):
        cd = self.cleaned_data
        if cd['cost_type'] == 1:
            if cd['weight'] is None or cd['weight'] <= 0:
                raise forms.ValidationError('重量不能为空或为零')
        return self.cleaned_data

    def save(self, commit=True):
        block_num = self.save(commit=False)
        cd = forms.ModelForm.cleaned_data
        if cd['cost_type'] == 2:
            cd['m3'] = (cd['long'] * cd['width'] * cd['high']) / 100000
        cd['batch'] = Batch.objects.filter(name=cd['batch'])[0]
        if commit:
            block_num.save()
            Product.objects.create(block_num=block_num, weight=cd['weight'], long=cd['long'], width=cd['width'],
                                   high=cd['high'], m3=cd['m3'], batch=cd['batch'], cost_type=cd['cost_type'],
                                   ps=cd['ps'])
        return block_num


purchase_form = forms.inlineformset_factory(PurchaseOrder, PurchaseOrderItem, form=PurchaseOrderItemForm)
