# _*_ conding:utf-8 _*_
__author__ = 'pbpoon'
__date__ = '2017/6/4 22:37'

from django import forms
from .models import PurchaseOrderItem, PurchaseOrder, ImportOrder, PaymentHistory, ImportOrderItem
from products.models import Product, Batch, Quarry, Category
from decimal import Decimal


class ImportOrderForm(forms.ModelForm):
    class Meta:
        model = ImportOrder
        fields = ['finish_pay', 'supplier', 'order_date', 'container', 'price', 'handler', 'ps', 'file']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['finish_pay', 'handler', 'date', 'supplier', 'cost_money', 'cost_by', 'ps', 'file']
        widgets = {
            'date': forms.TextInput(attrs={'class': 'dt'})
        }


class PurchaseOrderItemForm(forms.ModelForm):
    category = forms.CharField(label='品种', max_length=16)
    quarry = forms.CharField(label='矿口', max_length=16)
    batch = forms.CharField(label='批次', max_length=16)
    block_name = forms.CharField(label='荒料编号', max_length=16, required=True)
    weight = forms.DecimalField(label='重量', max_digits=9, decimal_places=2, help_text='单位为：吨', required=False)
    long = forms.IntegerField(label='长', help_text='单位：厘米', required=False)
    width = forms.IntegerField(label='宽', help_text='单位：厘米', required=False)
    high = forms.IntegerField(label='高', help_text='单位：厘米', required=False)
    m3 = forms.DecimalField(label='立方', max_digits=9, decimal_places=2, help_text='单位为：立方米', required=False)
    price = forms.DecimalField(label='价格', max_digits=9, decimal_places=2)
    ps = forms.CharField(label='备注信息', required=False)

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'
        widgets = {
            'block_name': forms.TextInput(attrs={'size': '4'}),
            'block_num': forms.HiddenInput(),
            'price': forms.TextInput(attrs={'size': '4'})
        }

    def clean(self):
        cd = self.cleaned_data
        cost_by = cd['order'].cost_by
        weight = cd['weight']
        block_num = cd['block_name']
        if Product.objects.filter(block_num=block_num).exists():
            raise forms.ValidationError('荒料编号[{}]已经有数据，请确保将保存的订单明细列表内的荒料编号的资料为全新！'.format(block_num))
        else:
            if cost_by == 'ton':
                if weight is None or weight <= 0:
                    raise forms.ValidationError('重量不能为空或为零')
            if cost_by == 'm3':
                if not cd['m3'] or cd['m3'] == 0:
                    if not cd['long'] or not cd['high'] or not cd['width']:
                        raise forms.ValidationError('重量不能为空或为零')
                    cd['m3'] = Decimal('{0:.2f}'.format(int(cd['long'] * cd['high'] * cd['width'] * 0.000001)))
        return self.cleaned_data

    def save(self, commit=True):
        cd = self.cleaned_data
        block_name = cd['block_name']
        cd['batch'], _ = Batch.objects.get_or_create(name=cd['batch'].upper())
        cd['quarry'], _ = Quarry.objects.get_or_create(name=cd['quarry'].upper())
        cd['category'], _ = Category.objects.get_or_create(name=cd['category'].upper())
        product_dict = {'weight': cd['weight'], 'long': cd['long'], 'width': cd['width'],
                        'high': cd['high'], 'm3': cd['m3'], 'batch': cd['batch'],
                        'ps': cd['ps'], 'quarry': cd['quarry'], 'category': cd['category']}
        cd['block_num'], _ = Product.objects.get_or_create(block_num=block_name, defaults=product_dict)
        instance = super(PurchaseOrderItemForm, self).save(commit=False)
        instance.block_num = cd['block_num']
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        super(PurchaseOrderItemForm, self).__init__(*args, **kwargs)
        if self.instance.order_id is not None:
            product = self.instance.block_num
            initial_data = {
                'batch': product.batch.name,
                'quarry': product.quarry.name,
                'category': product.category.name,
                'block_name': product.block_num,
                'weight': product.weight,
                'long': product.long,
                'width': product.width,
                'high': product.high,
                'm3': product.m3,
                'ps': product.ps
            }
            self.initial.update(initial_data)


class ImportOrderItemForm(forms.ModelForm):
    category = forms.CharField(label='品种', max_length=16)
    quarry = forms.CharField(label='矿口', max_length=16)
    batch = forms.CharField(label='批次', max_length=16)
    block_name = forms.CharField(label='荒料编号', max_length=16, required=True)
    # weight = forms.DecimalField(label='重量', max_digits=9, decimal_places=2, help_text='单位为：吨', required=False)
    long = forms.IntegerField(label='长', help_text='单位：厘米', required=False)
    width = forms.IntegerField(label='宽', help_text='单位：厘米', required=False)
    high = forms.IntegerField(label='高', help_text='单位：厘米', required=False)
    m3 = forms.DecimalField(label='立方', max_digits=9, decimal_places=2, help_text='单位为：立方米', required=False)
    price = forms.DecimalField(label='价格', max_digits=9, decimal_places=2)
    ps = forms.CharField(label='备注信息', required=False)

    class Meta:
        model = ImportOrderItem
        fields = '__all__'
        widgets = {
            'block_num': forms.HiddenInput()
        }

    def clean_block_name(self):
        block_num = self.cleaned_data['block_name']
        try:
            product = Product.objects.get(block_num=block_num)
        except Exception as e:
            raise forms.ValidationError(f'荒料编号[{block_num}]不存在采购资料，请检查！')
        else:
            if ImportOrderItem.objects.filter(block_num=product):
                raise forms.ValidationError(f'荒料编号[{block_num}]已有进口报关运输资料，不能重复输入，请检查！')
        return block_num

    def save(self, commit=True):
        cd = self.cleaned_data
        block_name = cd['block_name']
        cd['block_num'] = Product.objects.get(block_num=block_name)
        instance = super(ImportOrderItemForm, self).save(commit=False)
        instance.block_num = cd['block_num']
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        super(ImportOrderItemForm, self).__init__(*args, **kwargs)
        if self.instance.order_id is not None:
            product = self.instance.block_num
            initial_data = {
                'batch': product.batch.name,
                'quarry': product.quarry.name,
                'category': product.category.name,
                'block_name': product.block_num,
                'weight': product.weight,
                'long': product.long,
                'width': product.width,
                'high': product.high,
                'm3': product.m3,
                'ps': product.ps,
            }
            self.initial.update(initial_data)


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


class PurchaseOrderItemBaseInlineFormset(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(PurchaseOrderItemBaseInlineFormset, self).__init__(*args, **kwargs)
        # for form in self.forms:
        #     form.empty_permitted = False

    def clean(self):
        block_list = []
        for form in self.forms:
            if form.cleaned_data.get('block_num'):
                block_num = form.cleaned_data['block_num']
                if block_num in block_list:
                    raise forms.ValidationError('荒料编号[{}]有重复数据'.format(block_num))
                block_list.append(block_num)
