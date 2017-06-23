from django.shortcuts import render, HttpResponseRedirect, redirect, HttpResponse
from django.http import JsonResponse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from .models import ProcessOrder, ServiceProvider, TSOrderItem, MBOrderItem, KSOrderItem, STOrderItem
from products.models import Product, Slab
from .forms import TSOrderItemForm, MBOrderItemForm, KSOrderItemForm, STOrderItemForm, ProcessOrderForm, SlabListForm, \
    SlabListItemForm, CustomBaseInlineFormset
from django.forms import inlineformset_factory
from utils import AddExcelForm

from django.db.models import Count, Sum

import xlrd
from decimal import Decimal
import json


class ServiceProviderListView(ListView):
    model = ServiceProvider


class ServiceProviderDetailView(DetailView):
    model = ServiceProvider


class ServiceProviderCreateView(CreateView):
    model = ServiceProvider
    fields = '__all__'


class ServiceProviderUpdateView(UpdateView):
    model = ServiceProvider
    fields = '__all__'


class ServiceProviderDeleteView(DeleteView):
    model = ServiceProvider
    success_url = reverse_lazy('process:serviceprovider_list')


class ProcessOrderListView(ListView):
    model = ProcessOrder


class ProcessOrderDetailView(DetailView):
    model = ProcessOrder

    def get_context_data(self, **kwargs):
        if self.object.order_type == 'TS':
            item_model = TSOrderItem
        elif self.object.order_type == 'MB':
            item_model = MBOrderItem
        elif self.object.order_type == 'KS':
            item_model = KSOrderItem
        elif self.object.order_type == 'ST':
            item_model = STOrderItem
        kwargs['item_list'] = item_model.objects.filter(order=self.object)
        return super(ProcessOrderDetailView, self).get_context_data(**kwargs)


class OrderFormsetMixin(object):
    def get_inlineformset(self):
        if self.object is not None:
            type = self.object.order_type
        else:
            type = self.request.GET.get('order_type', None)
        if type is None:
            raise '传入数据出错'
        if type == 'TS':
            model = TSOrderItem
            form = TSOrderItemForm
            fields = (
                'block_num', 'block_type', 'be_from', 'destination', 'quantity', 'unit', 'price',
                'date', 'ps')
        elif type == 'KS':
            model = KSOrderItem
            form = KSOrderItemForm
            fields = (
                'block_num', 'thickness', 'pic', 'pi', 'quantity', 'unit', 'price',
                'date', 'ps')
        elif type == 'MB':
            return MBOrderItemForm

        elif type == 'ST':
            model = STOrderItem
            form = STOrderItemForm
        return inlineformset_factory(self.model, model, form=form, formset=CustomBaseInlineFormset, fields=fields,
                                     extra=1)

    def get_context_data(self, **kwargs):
        context = super(OrderFormsetMixin, self).get_context_data(**kwargs)
        if self.kwargs.get('pk'):
            self.object = ProcessOrder.objects.get(id=self.kwargs.get('pk'))
        else:
            self.object = None
        formset = self.get_inlineformset()
        if self.object:
            instance = self.object
        else:
            instance = ProcessOrder()
        if self.request.method == 'POST':
            context['form'] = ProcessOrderForm(self.request.POST, instance=instance)
            context['formset'] = formset(self.request.POST, instance=instance)
        else:
            context['form'] = ProcessOrderForm(instance=instance)
            context['formset'] = formset(instance=instance)
        return context


class ProcessOrderCreateView(OrderFormsetMixin, TemplateView):
    model = ProcessOrder
    template_name = 'process/processorder_form.html'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        form = context['form']
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            object = form.save()
            formset.save()
            # success_url =
            return reverse(object.get_absolute_url)
        else:
            return self.render_to_response({'form': form, 'formset': formset})


class ProcessMbOrderEditView(TemplateView):
    template_name = 'process/processorder_mb_form.html'

    def get_context_data(self, **kwargs):
        context = super(ProcessMbOrderEditView, self).get_context_data(**kwargs)
        if self.kwargs.get('pk'):
            self.object = ProcessOrder.objects.get(id=self.kwargs.get('pk'))
        else:
            self.object = None
        if self.object:
            instance = self.object
        else:
            instance = ProcessOrder()
        if self.request.method == 'POST':
            context['form'] = ProcessOrderForm(self.request.POST, instance=instance)
            context['item_form'] = AddExcelForm(self.request.POST, self.request.FILES)
        else:
            context['form'] = ProcessOrderForm(instance=instance)
            context['item_form'] = AddExcelForm()
        return context


class GetBlockListView(View):
    def get(self, request):
        block_list = Product.objects.filter(id__in=[1, 2, 3])
        block_list = serializers.serialize('json', block_list)
        data = {
            'block_list': block_list
        }
        return JsonResponse(data, safe=False)


class ImportSlabList(View):
    def post(self, request, *args, **kwargs):
        item_form = AddExcelForm(request.POST, request.FILES)
        if item_form.is_valid():
            f = item_form.files.get('file')
            if f:
                data = xlrd.open_workbook(file_contents=f.read())
                table = data.sheets()[0]
                nrows = table.nrows  # 总行数
                colnames = table.row_values(0)  # 表头列名称数据
                list = []
                for rownum in range(1, nrows):
                    rows = table.row_values(rownum)
                    item = {}
                    for key, row in zip(colnames, rows):
                        if key == 'part_num':
                            item[key] = str(row).split('.')[0]
                        elif key == 'block_num':
                            item[key] = Product.objects.filter(block_num=str(row).split('.')[0])[0]
                        elif key == 'line_num':
                            item[key] = int(row)
                        else:
                            if row:
                                item[key] = Decimal('{0:.2f}'.format(row))
                            # else:
                            #     item[key] = ''
                    list.append(Slab(**item))
                print(list)
                id_list = []
                for i in list:
                    i.save()
                    id_list.append(i.id)
                block_item = Slab.objects.filter(id__in=id_list).values('block_num', 'thickness').annotate(
                    pics=Count('id'),
                    m2=Sum('m2'))
                print(block_item)
                for item in block_item:
                    item['item'] = [slab.id for slab in list if
                                    slab.block_num_id == item['block_num'] and slab.thickness == item['thickness']]
        return HttpResponse(block_item)
        # {block_num: 8801, thickness: 1.5, pics: 48, part: 3, m2: 283.53,
        #  slab: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}



        #         if PurchaseOrderItem.objects.filter(block_num=row[0]):
        #             if not ImportOrderItem.objects.filter(
        #                     block_num=PurchaseOrderItem.objects.filter(block_num=row[0])):
        #                 """
        #                 以后还有再加一个判断该编号荒料有没有到货记录。
        #                 """
        #                 block_num = PurchaseOrderItem.objects.get(block_num=row[0])
        #                 order_item.append(
        #                     ImportOrderItem(block_num=block_num, weight=row[1]))
        #                 block = Product.objects.get(block_num=block_num)
        #                 block.weight = row[1]
        #                 block_list.append(block)
        #         else:
        #             error.append(row[0])
        #     if len(error) != 0:
        #         messages.error(self.request, '荒料编号:{}，已有数据，请检查清楚！'.format("，".join(error)))
        #         context = {
        #             'object': object,
        #             'form': form,
        #             'file_form': file_form,
        #         }
        #         return render(self.request, self.template_name, context)
        # if self.request.POST.get('save'):
        #     object.save()
        #     for block_id, block in zip(order_item, block_list):
        #         block_id.order = object
        #         block_id.save()
        #         block.save()
        #     messages.success(self.request, '数据已经成功保存!')
        #     success_url = object.get_absolute_url()
        #     return HttpResponseRedirect(success_url)
        # messages.success(self.request, '数据已经成功保存!')
        # context = {
        #     # 'object': object,
        #     'block_list': block_list,
        #     'form': form,
        #     'file_form': file_form,
        #     'total_weight': '{0:.2f}'.format(sum(float(i.weight) for i in block_list)),
        #     'total_count': len(block_list),
        # }
        # return render(self.request, self.template_name, context)
