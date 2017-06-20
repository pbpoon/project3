from django.shortcuts import render, HttpResponseRedirect
from django.http import JsonResponse
from django.core import serializers
from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from .models import ProcessOrder, ServiceProvider, TSOrderItem, MBOrderItem, KSOrderItem, STOrderItem
from products.models import Product
from .forms import TSOrderItemForm, MBOrderItemForm, KSOrderItemForm, STOrderItemForm, ProcessOrderForm
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.db import transaction


class CustomBaseInlineFormset(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        block_list = []
        for form in self.forms:
            block_num = form.cleaned_data['block_num']
            if block_num in block_list:
                raise forms.ValidationError('荒料编号不能重复')
            block_list.append(block_num)


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
        elif type == 'KS':
            model = KSOrderItem
            form = KSOrderItemForm
        elif type == 'MB':
            model = MBOrderItem
            form = MBOrderItemForm
        elif type == 'ST':
            model = STOrderItem
            form = STOrderItemForm
        return inlineformset_factory(self.model, model, form=form, fields='__all__', extra=1)

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
            success_url = object.get_absolute_url
            return HttpResponseRedirect(success_url)
        else:
            return self.render_to_response({'form': form, 'formset': formset})


class GetBlockListView(View):
    def get(self, request):
        block_list = Product.objects.filter(id__in=[1, 2, 3])
        block_list = serializers.serialize('json', block_list)
        data = {
            'block_list': block_list
        }
        return JsonResponse(data, safe=False)
