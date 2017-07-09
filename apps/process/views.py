from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.core import serializers

from django.core.urlresolvers import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, \
    DeleteView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ProcessOrder, ServiceProvider, TSOrderItem, MBOrderItem, \
    KSOrderItem, STOrderItem, SlabList, SlabListItem
from products.models import Product, Slab
from .forms import TSOrderItemForm, MBOrderItemForm, KSOrderItemForm, \
    STOrderItemForm, ProcessOrderForm, SlabListForm, \
    SlabListItemForm, CustomBaseInlineFormset
from products.forms import SlabModelFormset, SlabForm
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
                'id', 'block_num', 'block_name', 'block_type', 'be_from',
                'destination', 'quantity', 'unit', 'price',
                'date', 'ps')
        elif type == 'KS':
            model = KSOrderItem
            form = KSOrderItemForm
            fields = (
                'id', 'block_num', 'block_name', 'thickness', 'pic', 'pi',
                'quantity', 'unit', 'price',
                'date', 'ps')
        elif type == 'MB':
            import_list = self.get_import_list()
            model = MBOrderItem
            form = MBOrderItemForm
            fields = (
                'id', 'block_num', 'block_name', 'thickness', 'pic', 'quantity',
                'unit', 'price',
                'date', 'ps')
            extra = len(import_list)
        elif type == 'ST':
            model = STOrderItem
            form = STOrderItemForm
        if self.object is not None:
            extra = 0
        return inlineformset_factory(parent_model=self.model, model=model,
                                     form=form, formset=CustomBaseInlineFormset,
                                     fields=fields,
                                     extra=extra, can_delete=True)

    def get_context_data(self, **kwargs):
        context = super(OrderFormsetMixin, self).get_context_data(**kwargs)

        self.order_type = self.get_order_type()

        formset = self.get_inlineformset()
        error = []
        if self.request.method == 'POST':
            context['itemformset'] = formset(self.request.POST, prefix='fs',
                                             instance=self.object)
        else:
            context['itemformset'] = formset(prefix='fs', instance=self.object)
            if self.order_type == 'MB':
                if self.object is None:
                    for form, data in zip(context['itemformset'],
                                          self.get_import_list()):
                        try:
                            block_num = Product.objects.get(
                                block_num=data['block_num'])
                        except Exception as e:
                            error.append('导入的码单中：荒料编号[{}]不存在，请查询'.format(
                                data['block_num']))
                        else:
                            form.initial = {
                                'block_name': data['block_num'],
                                'block_num': block_num,
                                'thickness': data['thickness'],
                                'pic': data['block_pics'],
                                'quantity': data['block_m2'],
                                'unit': 'm2'
                            }
            context['errors'] = error
            context['order_type'] = self.order_type
            context['data_list'] = self.get_block_num_datalist()
        return context

    def save_import_data(self):
        cart = Cart(self.request)
        slab_lst = []
        lst = cart.cart['import_slabs']
        for item in lst:
            item['block_num'] = Product.objects.get(block_num=item['block_num'])
            slab = Slab.objects.create(**item)
            SlabList()
            slab_lst.append(slab)
        return slab_lst

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
        return cart.make_import_slab_list()

    def get_block_num_datalist(self):
        if self.order_type == 'KS':
            block_lst = Product.objects.filter(ksorderitem_cost__isnull=True)
        elif self.order_type == 'MB':
            block_lst = Product.objects.filter(ksorderitem_cost__isnull=False)
        elif self.order_type == 'ST':
            block_lst = Product.objects.filter(tsorderitem_cost__isnull=True)
        else:
            block_lst = Product.objects.all()
        return block_lst

    def form_valid(self, form):
        data = self.get_context_data()
        formset = data['itemformset']

        with transaction.atomic():
            sid = transaction.savepoint()
            instance = form.save()
            if formset.is_valid():
                formset.instance = instance
                items = formset.save()
                if self.order_type == 'MB':
                    cart = Cart(self.request)
                    for item in items:
                        slab_lst = cart.get_import_slab_list_by_parameter(block_num=item.block_num,
                                                                          thickness=item.thickness)
                        slablist = SlabList.objects.create(order=item,
                                                           data_entry_staff=self.request.user)
                        for i in slab_lst:
                            i['block_num'] = Product.objects.get(
                                block_num=i['block_num']).id
                            slabform = SlabForm(data=i)
                            if slabform.is_valid():
                                slab = slabform.save()
                            # slab = Slab.objects.create(**i)
                            slab_list_item_data = {'slab': slab.id, 'slablist': slablist.id,
                                                   'part_num': slab.part_num, 'line_num':
                                                       slab.line_num}
                            slab_list_item_form = SlabListItemForm(data=slab_list_item_data)

                            if slab_list_item_form.is_valid():
                                slab_list_item_form.save()
                                # SlabList.objects.create(slablist=slablist.id, slab=slab.id,
                                #                         part_num=slab.part_num,
                                #                         line_num=slab.line_num)
                                # lst = cart.cart['import_slabs']
                                # productfomset = SlabModelFormset(data=lst)
                                # if productfomset.is_valid():
                                #     productfomset.save()

                    for item in items:
                        cart.remove_import_slabs(
                            block_num=item.block_num,
                            thickness=str(item.thickness))
                # success_url = 'process:order_list'
                # return redirect(success_url)
                return super(OrderFormsetMixin, self).form_valid(form)
            else:
                transaction.savepoint_rollback(sid)
                context = {
                    'order_type': self.get_order_type(),
                    'form': form,
                    'itemformset': formset,
                    'data_list': self.get_block_num_datalist()
                }
        return self.render_to_response(context)

    def get_initial(self):
        if self.object is None:
            initial = {'data_entry_staff': self.request.user}
            return initial
        return super(OrderFormsetMixin, self).get_initial()


class ProcessOrderCreateView(LoginRequiredMixin, OrderFormsetMixin, CreateView):
    model = ProcessOrder
    form_class = ProcessOrderForm


class ProcessOrderUpdateView(LoginRequiredMixin, OrderFormsetMixin, UpdateView):
    model = ProcessOrder
    form_class = ProcessOrderForm
