from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers
from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from .models import ProcessOrder, ServiceProvider, TSOrderItem, MBOrderItem, KSOrderItem, STOrderItem
from products.models import Product
from .forms import TSOrderItemForm, MBOrderItemForm, KSOrderItemForm, STOrderItemForm
from django.forms import inlineformset_factory


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


class OrderFormsetMixin(object):
    def get_inlineformset(self):
        if self.object:
            type = self.object.order_type
        else:
            type = self.request.GET.get('order_type', None)
        if type is None:
            raise '传入数据出错'
        if type == 'TS':
            model = TSOrderItem
            form = TSOrderItemForm
        elif type == 'KS':
            model = KSOrderItem
            form = KSOrderItemForm
        elif type == 'MB':
            model = MBOrderItem
            form = MBOrderItemForm
        elif type == 'ST':
            model = STOrderItem
            form = STOrderItemForm
        return inlineformset_factory(self.model, model, form=form, fields='__all__')

    def get_context_data(self, **kwargs):
        formset = self.get_inlineformset()
        if self.request.method == 'POST':
            kwargs['formset'] = formset(self.request.POST)
        else:
            kwargs['formset'] = formset()
        return super(OrderFormsetMixin, self).get_context_data(**kwargs)


class ProcessOrderCreateView(OrderFormsetMixin, CreateView):
    model = ProcessOrder
    fields = '__all__'


class GetBlockListView(View):
    def get(self, request):
        block_list = Product.objects.filter(id__in=[1, 2, 3])
        block_list = serializers.serialize('json', block_list)
        data = {
            'block_list': block_list
        }
        return JsonResponse(data, safe=False)
