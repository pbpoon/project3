from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, \
    TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic.detail import BaseDetailView, SingleObjectTemplateResponseMixin, \
    SingleObjectMixin

from cart.cart import Cart
from process.forms import SlabListItemForm
from process.models import SlabList, SlabListItem
from process.views import SaveCurrentOrderSlabsMixin
from products.models import Product, Slab
from .models import CustomerInfo, Province, City, SalesOrder, SalesOrderItem
from .forms import SalesOrderForm, CustomerInfoForm, SalesOrderItemForm, OrderPriceForm
from django.forms import inlineformset_factory, formset_factory, modelformset_factory

from utils import AddExcelForm, ImportData
from decimal import Decimal


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


class SalesOrderDetailView(SaveCurrentOrderSlabsMixin, DetailView):
    model = SalesOrder

    def get_context_data(self, **kwargs):
        kwargs['item_list'] = self.object.items.all()
        kwargs['total_amount'] = '{:.0f}'.format(
            sum(Decimal(item.sum) for item in self.object.items.all()))
        kwargs['total_count'] = self.object.items.all().count()
        kwargs['total_pic'] = sum(int(item.pic) for item in self.object.items.all())
        kwargs['total_part'] = sum(int(item.part) for item in self.object.items.all() if item.part)
        kwargs['total_quantity'] = '{:.2f}'.format(
            sum(Decimal(item.quantity) for item in self.object.items.all()))
        return super(SalesOrderDetailView, self).get_context_data(**kwargs)


class SalesOrderEditMixin:
    """
    formset_model = 生成formset的model
    formset_fields = formset的字段，默认生成所有字段
    formset_prefix = formset使用的prefix，默认'fs'
    """
    formset_model = None
    formset_class = SalesOrderItemForm
    formset_fields = '__all__'
    formset_prefix = 'fs'

    def get_formset_fields(self):
        return self.formset_fields

    def get_formset_prefix(self):
        return self.formset_prefix

    def get_formset_class(self):
        extra = 0 if self.object else \
            len(
                self.get_cart().make_slab_list())  # len(self.get_cart().make_slab_list(keys='current_order_slab_ids'))
        return inlineformset_factory(self.model, self.formset_model, form=self.formset_class,
                                     extra=extra, fields=self.get_formset_fields())

    def get_formset_kwargs(self):
        return self.get_cart().make_slab_list(keys='current_order_slab_ids') if self.object else \
            self.get_cart().make_slab_list()

    def get_formset(self):
        if self.request.GET.get('next'):
            formset = self.get_formset_class()(data=self.request.GET,
                                               prefix=self.get_formset_prefix(),
                                               instance=self.object)
        elif self.request.method in ('POST', 'PUT'):
            formset = self.get_formset_class()(data=self.request.POST,
                                               prefix=self.get_formset_prefix(),
                                               instance=self.object)
        else:
            formset = self.get_formset_class()(instance=self.object,
                                               prefix=self.get_formset_prefix())

        return self.make_formset_initial(formset)

    def make_formset_initial(self, formset):
        """
        是这个mixin可以适应更多order的formset，不同的order只需要更改这里来适配
        :param formset:
        :return:
        """
        for form, data in zip(formset, self.get_formset_kwargs()):
            data['block_num'] = Product.objects.get(block_num=data['block_num'])
            form.initial.update({
                'block_num': data['block_num'],
                'part': data['part_count'],
                'pic': data['block_pics'],
                'quantity': data.get('quantity', data['block_m2']),
                'unit': 'ton' if data.get('quantiy') else 'm2',
                'thickness': data['thickness']
            })
        return formset

    def formset_valid(self, instance=None, formset=None):
        """
        :param instance:
        :param formset:
        :return: 如果保存过程出错返回错误'errors'和formset，如果成功，返回False。可以用if formset_valid（）
        """
        formset.instance = instance
        formset.save()
        errors = []
        if self.object:
            """
            编辑状态
            """
            slab_model = ContentType.objects.get_for_model(self.object)
            slab_list = SlabList.objects.get(content_type__pk=slab_model.id,
                                             object_id=self.object.id)
            order_ids = [str(slab.slab.id) for slab in
                         SlabListItem.objects.filter(slablist=slab_list).all()]
            ids = self.get_cart().cart['current_order_slab_ids']
            new_ids = set(ids) - set(order_ids)
            del_ids = set(order_ids) - set(ids)
            slabs = [
                {'slab': Slab.objects.get(id=slab),
                 'part_num': Slab.objects.get(id=slab).part_num,
                 'line_num': Slab.objects.get(id=slab).line_num}
                for slab in new_ids
                ]
            for i in slabs:
                slablistform = SlabListItemForm(data=i)
                if slablistform.is_valid():
                    slablistform.save()
                else:
                    errors.append(slablistform.errors)
            SlabListItem.objects.filter(slablist=slab_list, slab__in=del_ids).delete()
        else:
            """
            新建状态
            """
            slab_list = SlabList.objects.create(order=instance,
                                                data_entry_staff_id=self.request.user.id)
            slabs = [
                {'slablist': slab_list.id,
                 'slab': Slab.objects.get(id=id).id,
                 'part_num': Slab.objects.get(id=id).part_num,
                 'line_num': Slab.objects.get(id=id).line_num}
                for id in self.get_cart().cart['slab_ids']]
            for i in slabs:
                slablistform = SlabListItemForm(data=i)
                if slablistform.is_valid():
                    slablistform.save()
                else:
                    errors.append(slablistform.errors)
            """
            把slab_list包含的slab id 读取出来，和选择的slab id作比较
            如果是新订单就把import_slab_list用get_import_slab_list_by_parameter遍历出来添加到列表，
            如果是编辑订单就直接读取cart的current_order_slab_ids，并用make_slab_list返回码单
            """
        if errors:
            context = {
                'itemformset': formset,
                'errors': errors
            }
            return context
        else:
            return False

    def get_cart(self):
        return Cart(self.request)


class SalesOrdeSaveMixin:
    def form_valid(self, form):
        formset = self.get_formset()
        with transaction.atomic():
            sid = transaction.savepoint()
            form.data_entry_staff = self.request.user
            instance = form.save()
            if formset.is_valid():
                formset_error = self.formset_valid(instance, formset)
                if formset_error:
                    transaction.savepoint_rollback(sid)
                    context = {
                        'form': form,
                        'itemformset': formset,
                        'errors': formset_error['errors']
                    }
                    return self.render_to_response(context)
            else:
                transaction.savepoint_rollback(sid)
                context = {
                    'form': form,
                    'itemformset': formset,
                    'errors': ""
                }
                return self.render_to_response(context)

        return super(SalesOrdeSaveMixin, self).form_valid(form)


class SalesOrderAddView(LoginRequiredMixin, SalesOrderEditMixin, TemplateView):
    template_name = 'sales/salesorder_create_step1.html'
    formset_model = SalesOrderItem

    def get_context_data(self, **kwargs):
        self.cart = Cart(self.request)
        formset = self.get_formset()
        for item, form in zip(self.get_formset_kwargs(), formset):
            item['form'] = form
        kwargs['item_list'] = self.cart.make_slab_list()
        return kwargs


class SalesOrderUpdateItemView(LoginRequiredMixin, SalesOrderEditMixin, DetailView):
    model = SalesOrder
    form_class = SalesOrderForm
    formset_model = SalesOrderItem
    template_name = 'sales/salesorder_form.html'

    def get_context_data(self, **kwargs):
        item_list = self.get_formset_kwargs()
        price_formset = self.get_formset()
        kwargs['item_list'] = zip(item_list, price_formset)
        kwargs['price_formset'] = price_formset
        return super(SalesOrderUpdateItemView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = self.get_formset()
        if formset.is_valid():
            formset_error = self.formset_valid(self.object, formset)
            if formset_error:
                context = {
                    'itemformset': formset,
                    'errors': formset_error['errors']
                }
                return self.render_to_response(context)
            return HttpResponseRedirect(self.object.get_absolute_url())


class SalesOrderCreateView(LoginRequiredMixin, SalesOrderEditMixin, SalesOrdeSaveMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    formset_model = SalesOrderItem

    def get_context_data(self,  **kwargs):
        price_formset = self.get_formset()
        step = self.request.GET.get('step') or self.request.POST.get('step')
        kwargs['item_list'] = ""
        if not step:
            item_list = self.get_formset_kwargs()
            for item in item_list:
                item['slab_ids'] = [id for part in item['part_num'].values() for id in
                                    part['slabs']]

            kwargs['item_list'] = zip(item_list, price_formset)
            kwargs['price_formset'] = price_formset
            kwargs['step'] = '1'
            kwargs['update'] = '1'
        elif step == '1':
            kwargs['step'] = '2'
            cd = price_formset.cleaned_data
            kwargs['total_quantity'] = '{:.2f}'.format(sum(item['quantity'] for item in cd))
            kwargs['total_amount'] = '{:.0f}'.format(
                sum(item['quantity'] * item['price'] for item in cd))
            kwargs['total_count'] = len(cd)
        return super(SalesOrderCreateView, self).get_context_data(**kwargs)


class SalesOrderUpdateInfoView(LoginRequiredMixin, UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name_suffix = '_info_form'
    # formset_fields = ('block_name', 'thickness', 'part', 'pic', 'quantity', 'unit', 'price',
    #                   'block_num', 'slab_list')


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
