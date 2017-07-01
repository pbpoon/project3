from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.core import serializers

from django.core.urlresolvers import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ProcessOrder, ServiceProvider, TSOrderItem, MBOrderItem, KSOrderItem, STOrderItem
from products.models import Product, Slab
from .forms import TSOrderItemForm, MBOrderItemForm, KSOrderItemForm, STOrderItemForm, ProcessOrderForm, SlabListForm, \
    SlabListItemForm, CustomBaseInlineFormset
from django.forms import inlineformset_factory
from utils import AddExcelForm

from cart.cart import Cart

from django.db import transaction


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
        extra = 1
        type = self.order_type
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
            import_list = self.get_import_list()
            model = MBOrderItem
            form = MBOrderItemForm
            fields = (
                'block_num', 'thickness', 'pic', 'quantity', 'unit', 'price',
                'date', 'ps')
            extra = len(import_list)
        elif type == 'ST':
            model = STOrderItem
            form = STOrderItemForm
        return inlineformset_factory(parent_model=self.model, model=model, form=form, formset=CustomBaseInlineFormset,
                                     fields=fields,
                                     extra=extra)

    def get_context_data(self, **kwargs):
        context = super(OrderFormsetMixin, self).get_context_data(**kwargs)
        if self.kwargs.get('pk'):
            self.object = ProcessOrder.objects.get(id=self.kwargs.get('pk'))
        else:
            self.object = None
        if self.object:
            instance = self.object
        else:
            instance = ProcessOrder()

        self.order_type = self.get_order_type()

        formset = self.get_inlineformset()

        if self.request.method == 'POST':
            context['form'] = ProcessOrderForm(self.request.POST, instance=instance)
            context['formset'] = formset(self.request.POST, instance=instance)
        else:
            context['form'] = ProcessOrderForm(instance=instance, initial=self.get_form_initial())

            context['formset'] = formset(instance=instance)
            if self.order_type == 'MB':
                if not self.object:
                    for form, data in zip(context['formset'], self.get_import_list()):
                        form.initial = {
                            'block_num': Product.objects.filter(block_num=data['block_num'])[0],
                            'thickness': data['thickness'],
                            'pic': data['block_pics'],
                            'quantity': data['block_m2'],
                            'unit': 'm2'
                        }
            context['order_type'] = self.order_type
            context['data_list'] = self.get_block_num_datalist()
        return context

    def get_order_type(self):
        if self.object:
            type = self.object.order_type
        elif self.request.POST.get('order_type', None):
            type = self.request.POST.get('order_type', None)
        else:
            type = self.request.GET.get('order_type', None)
        if type is None:
            raise ValueError('传入数据出错!')
        return type

    def get_import_list(self):
        cart = Cart(self.request)
        return cart.show_import_slab_list()

    def get_form_initial(self):
        if not self.object:
            initial = {
                'order_type': self.order_type
            }
        else:
            initial = {}
        return initial

    def get_block_num_datalist(self):
        if self.order_type == 'KS':
            block_lst = Product.objects.filter(ksorderitem_cost__isnull=True)
        elif self.order_type == 'MB':
            block_lst = Product.objects.filter(ksorderitem_cost__isnull=False)
        elif self.order_type == 'TS':
            block_lst = Product.objects.filter(tsorderitem_cost__isnull=True)
        else:
            block_lst = Product.objects.all()
        return block_lst


class ProcessOrderCreateView(LoginRequiredMixin, OrderFormsetMixin, TemplateView):
    model = ProcessOrder
    template_name = 'process/processorder_form.html'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        form = context['form']
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.data_entry_staff = request.user
                self.object.save()
                formset.instance = self.object
                items = formset.save()
                cart = Cart(request)
                for item in items:
                    cart.remove_import_slabs(block_num=item.block_num.block_num_id, thickness=str(item.thickness))
            success_url = 'process:order_list'
            return redirect(success_url)
        else:
            context = {
                'order_type': self.get_order_type(),
                'form': form,
                'formset': formset
            }
            return self.render_to_response(context)


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
            context['item_form'] = MBOrderItemForm(self.request.POST, self.request.FILES)
        else:
            context['form'] = ProcessOrderForm(instance=instance)
            context['item_form'] = AddExcelForm()
        return context


import json


def get_block_list(request):
    if request.is_ajax():
        return HttpResponse(json.dumps({'message': 'awesome'}, ensure_ascii=False), mimetype='application/javascript')



        #         data = xlrd.open_workbook(file_contents=f.read())
        #         table = data.sheets()[0]
        #         nrows = table.nrows  # 总行数
        #         colnames = table.row_values(0)  # 表头列名称数据
        #         list = []
        #         for rownum in range(1, nrows):
        #             rows = table.row_values(rownum)
        #             item = {}
        #             for key, row in zip(colnames, rows):
        #                 if key == 'part_num':
        #                     item[key] = str(row).split('.')[0]
        #                 elif key == 'block_num':
        #                     item[key] = Product.objects.filter(block_num=str(row).split('.')[0])[0]
        #                 elif key == 'line_num':
        #                     item[key] = int(row)
        #                 else:
        #                     if row:
        #                         item[key] = Decimal('{0:.2f}'.format(row))
        #                     # else:
        #                     #     item[key] = ''
        #             list.append(Slab(**item))
        #         print(list)
        #         id_list = []
        #         for i in list:
        #             i.save()
        #             id_list.append(i.id)
        #         block_item = Slab.objects.filter(id__in=id_list).values('block_num', 'thickness').annotate(
        #             pics=Count('id'),
        #             m2=Sum('m2'))
        #         print(block_item)
        #         for item in block_item:
        #             item['item'] = [slab.id for slab in list if
        #                             slab.block_num_id == item['block_num'] and slab.thickness == item['thickness']]
        # return HttpResponse(block_item)
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
