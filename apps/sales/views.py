from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin

from cart.cart import Cart
from products.models import Product
from .models import CustomerInfo, Province, City, SalesOrder, SalesOrderItem
from .forms import SalesOrderForm, CustomerInfoForm, SalesOrderItemForm
from django.forms import inlineformset_factory

from utils import AddExcelForm, ImportData


class ProvinceCityInfoMixin(object):
    def get_context_data(self, *args, **kwargs):
        kwargs['province_lst'] = Province.objects.all()
        kwargs['city_lst'] = City.objects.all()
        return super(ProvinceCityInfoMixin, self).get_context_data(*args, **kwargs)


class CustomerInfoListView(LoginRequiredMixin, ListView):
    model = CustomerInfo


class CustomerInfoDetailView(LoginRequiredMixin, DetailView):
    model = CustomerInfo


class CustomerInfoCreateView(LoginRequiredMixin, CreateView):
    model = CustomerInfo
    form_class = CustomerInfoForm
    # fields = '__all__'


class CustomerInfoUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomerInfo
    fields = '__all__'


class CustomerInfoDeleteView(LoginRequiredMixin, DeleteView):
    model = CustomerInfo


class SalesOrderListView(ListView):
    model = SalesOrder


class SalesOrderDetailView(DetailView):
    model = SalesOrder


class SalesOrderEditMixin:
    """
    formset_model = 生成formset的model
    formset_fields = formset的字段，默认生成所有字段
    formset_prefix = formset使用的prefix，默认'fs'
    """
    formset_model = None
    formset_fields = '__all__'
    formset_prefix = 'fs'

    def get_formset_class(self):
        extra = len(self.cart.make_slab_list(keys='current_order_slab_ids')) if self.object else \
            len(self.cart.make_slab_list())
        return inlineformset_factory(self.model, self.formset_model, form=SalesOrderItemForm,
                                     extra=extra, fields=self.formset_fields)

    def get_formset_kwargs(self):
        return self.cart.make_slab_list(keys='current_order_slab_ids') if self.object else \
            self.cart.make_slab_list()

    def get_formset(self):
        if self.request.method in ('POST', 'PUT'):
            formset = self.get_formset_class()(self.request.POST, prefix=self.formset_prefix,
                                               instance=self.object)
        else:
            formset = self.get_formset_class()(instance=self.object, prefix=self.formset_prefix)
        for form, data in zip(formset, self.get_formset_kwargs()):
            data['block_name'] = data['block_num']
            data['block_num'] = Product.objects.get(block_num=data['block_num'])
            form.initial.update({
                'block_name': data['block_name'],
                'block_num': data['block_num'],
                'part': data['part_count'],
                'pic': data['block_pics'],
                'quantity': data.get('quantity', data['block_m2']),
                'unit': 'ton' if data.get('quantiy') else 'm2',
                'thickness': data['thickness']
            })
        return formset

    def get_context_data(self, *args, **kwargs):
        self.cart = Cart(self.request)
        kwargs['itemformset'] = self.get_formset()
        return super(SalesOrderEditMixin, self).get_context_data(*args, **kwargs)


class SalesOrderCreateView(LoginRequiredMixin, SalesOrderEditMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    formset_model = SalesOrderItem


class SalesOrderUpdateView(LoginRequiredMixin, SalesOrderEditMixin, UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    formset_model = SalesOrderItem


class SalesOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = SalesOrder


class ImportView(FormView):
    """
    导入省份，城市数据
    """
    data_type = 'city'
    template_name = 'sales/customerinfo_form.html'
    form_class = AddExcelForm

    def form_valid(self, form):
        f = form.files.get('file')
        model = Province if self.data_type == 'sheng' else City
        import_data = ImportData(f, data_type='sheng').data
        for i in import_data:
            model.objects.create(**i)
        return HttpResponse('0k')


def get_city_info(request):
    """
    ajax取省份下城市option
    :param request:
    :return: 字典
    """
    province_id = request.GET.get('province_id')
    father_id = Province.objects.get(pk=province_id).province_id
    city_lst = [{'id': city.id, 'name': city.name} for city in \
                City.objects.filter(father_id=father_id).all()]
    return JsonResponse(city_lst, safe=False)
