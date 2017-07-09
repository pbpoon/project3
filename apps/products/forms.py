# _*_ conding:utf-8 _*_
__author__ = 'pbpoon'
__date__ = '2017/6/4 22:33'

from django import forms
from .models import Product, Slab

import json


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['block_num', 'weight', 'long', 'width', 'high', 'm3', 'batch',
                   'ps']


class SlabForm(forms.ModelForm):
    class Meta:
        model = Slab
        exclude = ('is_sell', 'is_pickup', 'is_booking')


class SlabModelBaseFormst(forms.BaseModelFormSet):
    def clean(self):
        block_lst = []
        # msg = []
        # for form in self.forms:
        #     cd = form.cleaned_data
        #     item = json.dumps({'block_num': cd['block_num'],
        #                        'thickness': cd['thickness']})
        #     if item not in block_lst:
        #         block_lst.append(item)
        # for item in block_lst:
        #     kwargs = json.loads(item)
        #     if Slab.objects.filter(**kwargs).exists():
        #         Slab.objects.get(**kwargs).ar


SlabModelFormset = forms.modelformset_factory(Slab, SlabForm,
                                              formset=SlabModelBaseFormst)
