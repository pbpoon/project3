from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import ProcessOrder, ServiceProvider, TSOrderItem, MBOrderItem, KSOrderItem
from django.forms import inlineformset_factory
from .forms import TSorderItemForm
from django import forms


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
            form = TSorderItemForm
        elif type == 'KS':
            model = KSOrderItem
        elif type == 'MB':
            model = MBOrderItem
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

    def post(self, request, *args, **kwargs):
        formset = self.get_inlineformset()
        formset = formset(self.request.POST)
        form = self.get_form()
        if form.is_valid() and formset.is_valid():
            instance = form.save(commit=False)
            instance.data_entry_staff = self.request.user
            instance.save()
            formset.save()
            return HttpResponseRedirect(reverse_lazy('process:order_list'))
