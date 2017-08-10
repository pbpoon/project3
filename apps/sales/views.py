from collections import defaultdict
from datetime import date, datetime

from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, \
    TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction

from cart.cart import Cart
from process.forms import SlabListItemForm
from process.models import SlabList, SlabListItem
from process.views import SaveCurrentOrderSlabsMixin
from products.models import Product, Slab
from .models import CustomerInfo, Province, City, SalesOrder, SalesOrderItem, SalesOrderPickUp, \
    SalesOrderPickUpItem, SalesOrderPickUpCost
from .forms import SalesOrderForm, CustomerInfoForm, SalesOrderItemForm, OrderPriceForm, \
    PickUpItemForm
from django.forms import inlineformset_factory, formset_factory, modelformset_factory

from utils import AddExcelForm, ImportData, item2sales
from decimal import Decimal


class PickUpOrderInfoMixin:
    def get_sales_order(self):
        try:
            salesorder = SalesOrder.objects.get(pk=self.kwargs.get('salesorder'))
            return salesorder
        except Exception as e:
            raise ValueError('没有输入正确的order')

    def get_order_item_can_pickup_ids(self):
        slab_ids = []
        block_ids = []
        for slab_list in self.get_sales_order().slab_list.all():
            for slab in slab_list.item.all():
                if not slab.slab.has_pickup:
                    slab_ids.append(str(slab.slab.id))

        for item in self.get_sales_order().items.all():
            if item.thickness == '荒料':
                if not Product.objects.get(block_num=item.block_num).pickup_item.exists():
                    block_ids.append(Product.objects.get(block_num=item.block_num).block_num)
        return {'slab_ids': slab_ids, 'block_ids': block_ids}

    def get_formset_kwargs(self):
        return self.get_cart().make_items_list(key='current_order') if self.object else \
            self.get_cart().make_items_list(key='can_pickup')

    def get_cart(self):
        return Cart(self.request)

    def _get_cost_formset_class(self):
        return inlineformset_factory(self.model, SalesOrderPickUpCost, fields='__all__', extra=1)

    def get_cost_formset(self):
        return self.instance_cost_formset()

    def instance_cost_formset(self):
        if self.request.GET.get('next'):
            formset = self._get_cost_formset_class()(data=self.request.GET,
                                                     prefix='cost_fs',
                                                     instance=self.object)
        elif self.request.method in ('POST', 'PUT'):
            formset = self._get_cost_formset_class()(data=self.request.POST,
                                                     prefix='cost_fs',
                                                     instance=self.object)
        else:
            formset = self._get_cost_formset_class()(instance=self.object,
                                                     prefix='cost_fs')
        return formset


class VerifyMixin(object):
    model = None

    def post(self, request, *args, **kwargs):
        self.order = self.get_order()
        path = request.META.get('HTTP_REFERER')
        type = self.get_operation_type()
        if self.check_status():
            self._process_type(type)  # 以不同的状态处理
        else:
            messages.error(request, '该订单不能通过审核!')
        return redirect(path)

    def _process_type(self, type):
        return getattr(self, f'process_{type}')()

    def process_verify(self):
        is_sell = []
        for list in self.order.slab_list.all():
            issell = set(item.slab.block_num.block_num for item in list.item.all() \
                         if item.slab.is_sell or item.slab.is_booking)
            is_sell.extend(issell)
        if not is_sell:
            self.order.status = 'V'
            self.order.verifier = self.request.user
            self.order.verify_date = datetime.now()
            self.order.save()
            for list in self.order.slab_list.all():
                for item in list.item.all():
                    slab = item.slab
                    slab.is_sell = True
                    slab.save()
            messages.success(self.request, '该订单已成功通过审核!')
        else:
            messages.error(self.request, '本订单荒料编号[{}]有部分已经销售,不能通过审核!'.format(
                ','.join(is_sell)))

    def process_cancel(self):
        if self.order.status == 'V':
            for list in self.order.slab_list.all():
                for item in list.item.all():
                    slab = item.slab
                    slab.is_sell = False
                    slab.save()
        self.order.status = 'M'
        if self.order.ps is None:
            self.order.ps = f'该订单由{self.request.user}于{datetime.now()}撤销审核!'
        else:
            self.order.ps += f'该订单由{self.request.user}于{datetime.now()}撤销审核!'
        self.order.verifier = None
        self.order.verify_date = None
        self.order.save()

    def process_close(self):
        if self.order.status == 'V':
            for list in self.order.slab_list.all():
                for item in list.item.all():
                    slab = item.slab
                    slab.is_sell = False
                    slab.save()

    def check_status(self):
        type = self.get_operation_type()
        if type == 'verify':
            allow = ('N', 'M')
        elif type == 'close':
            allow = ('N', 'V', 'M')
        elif type == 'finish':
            allow = ('V',)
        elif type == 'cancel':
            allow = ('V',)
        if self.order.status in allow:
            return True
        else:
            return False

    def get_order(self):
        order = self.request.POST.get('order', None)
        if order:
            if self.model:
                return self.model.objects.filter(order=order).all()[0]
            else:
                raise ValueError('没有定义model')
        else:
            return self.get_object()

    def get_operation_type(self):
        p = self.request.POST
        if p.get('verify'):
            type = 'verify'
        elif p.get('close'):
            type = 'close'
        elif p.get('cancel'):
            type = 'cancel'
        elif p.get('finish'):
            type = 'finish'
        elif p.get('proceeds'):
            type = 'proceeds'
        return type


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


class SalesOrderDetailView(SaveCurrentOrderSlabsMixin, PickUpOrderInfoMixin, VerifyMixin,
                           DetailView):
    model = SalesOrder

    def get_context_data(self, **kwargs):
        super(SalesOrderDetailView, self).get_context_data(**kwargs)
        cart = Cart(self.request)
        order_ids = self.get_order_item_can_pickup_ids()
        cart.cart['can_pickup_block_ids'], \
        cart.cart['can_pickup_slab_ids'] = order_ids['block_ids'], order_ids['slab_ids']
        cart.cart['first_status'] = [1]  # 下标志
        cart.save()
        ids = []
        for item in self.object.items.all():
            if item.thickness == '荒料':
                ids.append(str(item.block_num))
        cart.cart['current_order_block_ids'] = ids if ids else []

        can_pickup_item_list = cart.make_items_list(key='can_pickup')
        kwargs['can_pickup_item_list'] = can_pickup_item_list
        can_pickup_dt = defaultdict(float)
        for item in can_pickup_item_list:
            can_pickup_dt[item['unit']] += float(item['quantity'])
        kwargs['can_pickup_total_quantity'] = {k: '{:.2f}'.format(v) for k, v in
                                               can_pickup_dt.items()}

        item_list = self.object.items.all()
        items = self.get_cart().make_items_list(key='current_order')
        kwargs['item_list'] = zip(item_list, items)
        kwargs['total_amount'] = '{:.0f}'.format(
            sum(Decimal(item.sum) for item in item_list))
        kwargs['total_count'] = self.object.items.all().count()
        kwargs['total_pic'] = sum(int(item.pic) for item in item_list)
        kwargs['total_part'] = sum(int(item.part) for item in item_list if item.part)
        item_dt = defaultdict(float)
        for item in item_list:
            item_dt[item.unit] += float(item.quantity)
        kwargs['total_quantity'] = {k: '{:.2f}'.format(v) for k, v in item_dt.items()}
        kwargs['already_pickup_list'] = self.object.pickup.all()
        return super(SalesOrderDetailView, self).get_context_data(**kwargs)

    def get_sales_order(self):
        return self.object


class SalesOrderEditMixin:
    """
    formset_model = 生成formset的model
    formset_fields = formset的字段，默认生成所有字段
    formset_prefix = formset使用的prefix，默认'fs'
    """
    formset_model = None
    formset_class = None
    formset_fields = '__all__'
    formset_prefix = 'fs'

    def _get_formset_fields(self):
        return self.formset_fields

    def _get_formset_prefix(self):
        return self.formset_prefix

    def _get_formset_class(self):
        extra = 0 if self.object else \
            len(self.get_formset_kwargs())
        return inlineformset_factory(self.model, self.formset_model, form=self.formset_class,
                                     extra=extra,
                                     fields=self._get_formset_fields())

    def get_formset_kwargs(self):
        return self.get_cart().make_items_list(key='current_order') if self.object else \
            self.get_cart().make_items_list()

    def get_formset(self):
        return self.make_formset_initial(self.instance_formset())

    def instance_formset(self):
        if self.request.GET.get('next'):
            formset = self._get_formset_class()(data=self.request.GET,
                                                prefix=self._get_formset_prefix(),
                                                instance=self.object)
        elif self.request.method in ('POST', 'PUT'):
            formset = self._get_formset_class()(data=self.request.POST,
                                                prefix=self._get_formset_prefix(),
                                                instance=self.object)
        else:
            formset = self._get_formset_class()(instance=self.object,
                                                prefix=self._get_formset_prefix())
        return formset

    def make_formset_initial(self, formset):
        # new_key = {'part_count': 'part', 'block_pics': 'pic'}

        for form, data in zip(formset, self.get_formset_kwargs()):
            data['block_num'] = Product.objects.get(block_num=data['block_num'])
            form.initial.update({
                'block_num': data['block_num'],
                'part': data['part_count'],
                'pic': data['block_pics'],
                'quantity': data['quantity'],
                'unit': data['unit'],
                'thickness': data['thickness']
            })
        # formset.initial = item2sales(self.get_formset_kwargs(), new_key)
        return formset

    def formset_valid(self, instance=None, formset=None):
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
                {'slab': Slab.objects.get(id=slab).id,
                 'part_num': Slab.objects.get(id=slab).part_num,
                 'line_num': Slab.objects.get(id=slab).line_num,
                 'slablist': slab_list.id}
                for slab in new_ids
                ]
            for slab in slabs:
                slablistform = SlabListItemForm(data=slab)
                if slablistform.is_valid():
                    slablistform.save()
                else:
                    errors.append(slablistform.errors)
            for id in new_ids:
                s = Slab.objects.get(id=id)
                s.is_booking = True
                s.save()
            for id in del_ids:
                s = Slab.objects.get(id=id)
                s.is_booking = False
                s.save()
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
            for slab in slabs:
                slablistform = SlabListItemForm(data=slab)
                if slablistform.is_valid():
                    slablistform.save()
                    s = Slab.objects.get(id=slab['slab'])
                    s.is_booking = True
                    s.save()
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


class SalesOrderSaveMixin:
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

        return super(SalesOrderSaveMixin, self).form_valid(form)


class SalesOrderAddView(LoginRequiredMixin, SalesOrderEditMixin, TemplateView):
    template_name = 'sales/salesorder_create_step1.html'
    formset_model = SalesOrderItem

    def get_context_data(self, **kwargs):
        self.cart = Cart(self.request)
        formset = self.get_formset()
        for item, form in zip(self.get_formset_kwargs(), formset):
            item['form'] = form
        kwargs['item_list'] = self.cart.make_items_list()
        return kwargs


class SalesOrderUpdateItemView(LoginRequiredMixin, SalesOrderEditMixin, DetailView):
    model = SalesOrder
    form_class = SalesOrderForm
    formset_class = SalesOrderItemForm
    formset_model = SalesOrderItem
    template_name = 'sales/salesorder_form.html'

    def get_context_data(self, **kwargs):
        item_list = self.get_formset_kwargs()
        price_formset = self.get_formset()
        kwargs['item_list'] = list(zip(item_list, price_formset))
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


class SalesOrderCreateView(LoginRequiredMixin, SalesOrderEditMixin, SalesOrderSaveMixin,
                           CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    formset_class = SalesOrderItemForm
    formset_model = SalesOrderItem

    def get_context_data(self, **kwargs):
        price_formset = self.get_formset()
        step = self.request.GET.get('step') or self.request.POST.get('step')
        kwargs['item_list'] = ""
        items = self.get_formset_kwargs()
        dt = defaultdict(float)
        for item in items:
            dt[item['unit']] += float(item['quantity'])
        kwargs['total_quantity'] = {k: '{:.2f}'.format(v) for k, v in dt.items()}
        kwargs['total_count'] = len(items)
        if not step:
            item_list = self.get_formset_kwargs()
            for item in item_list:
                item['slab_ids'] = [id for part in item['part_num'].values() for id in
                                    part['slabs']] if item['thickness'] != '荒料' else ''

            kwargs['item_list'] = list(zip(item_list, price_formset))
            kwargs['price_formset'] = price_formset
            kwargs['step'] = '1'
        elif step == '1':
            kwargs['step'] = '2'
            cd = price_formset.cleaned_data
            kwargs['total_amount'] = '{:.0f}'.format(
                sum(item['quantity'] * item['price'] for item in cd))
        return super(SalesOrderCreateView, self).get_context_data(**kwargs)


class SalesOrderUpdateInfoView(LoginRequiredMixin, UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name_suffix = '_info_form'
    # formset_fields = ('block_name', 'thickness', 'part', 'pic', 'quantity', 'unit', 'price',
    #                   'block_num', 'slab_list')


class SalesOrderDeleteView(LoginRequiredMixin, DeleteView):
    model = SalesOrder


class PickUpCreateView(LoginRequiredMixin, PickUpOrderInfoMixin, SalesOrderEditMixin,
                       SalesOrderSaveMixin, CreateView):
    model = SalesOrderPickUp
    fields = ['cart_num', 'consignee', 'date', 'ps']
    formset_model = SalesOrderPickUpItem
    formset_class = PickUpItemForm
    formset_fields = ['block_num', 'part', 'pic', 'thickness', 'quantity', 'unit']

    def get_first_status(self):
        try:
            first_status = self.get_cart().cart['first_status'].pop()
        except Exception as e:
            first_status = None
        return first_status

    def get_context_data(self, **kwargs):
        step = self.request.GET.get('step') or self.request.POST.get('step')
        self.first_status = self.get_first_status()
        if self.first_status:
            self.get_cart().cart['current_order_block_ids'] = self.get_cart().cart[
                'current_order_slab_ids'] = []
            self.get_cart().save()
        formset = self.get_formset()
        items = self.make_items()
        dt = defaultdict(float)
        for item in items:
            dt[item['unit']] += float(item['quantity'])
        for item in items:
            item['slab_ids'] = [id for part in item['part_num'].values() for id in
                                part['slabs']] if item['thickness'] != '荒料' else []
        kwargs['total_quantity'] = {k: '{:.2f}'.format(v) for k, v in dt.items()}
        kwargs['total_count'] = len(items)
        kwargs['cost_formset'] = self.get_cost_formset()
        kwargs['item_list'] = list(zip(items, formset))
        kwargs['price_formset'] = formset
        if not step:
            kwargs['step'] = '1'
        elif step == '1':
            kwargs['step'] = '2'
        elif step == '2':
            kwargs['step'] = '3'
        return super(PickUpCreateView, self).get_context_data(**kwargs)

    def get_formset_kwargs(self):
        return self.get_cart().make_items_list(key='current_order') if self.object else \
            self.make_items()

    def make_items(self):
        all_can_pickup_items = self.get_cart().make_items_list(key='can_pickup')
        for item in all_can_pickup_items:
            item['part_count'] = '0'
            item['block_pics'] = '0'
            item['quantity'] = '0'
            item['can_pickup'] = True
        choose_items = self.get_cart().make_items_list(key='current_order')
        choose_items_list = [(item['block_num'], item['thickness']) for item in choose_items]
        for item in all_can_pickup_items:
            if (item['block_num'], item['thickness']) not in choose_items_list:
                choose_items.append(item)

        return choose_items

    def form_valid(self, form):
        formset = self.get_formset()
        cost_formset = self.get_cost_formset()
        with transaction.atomic():
            sid = transaction.savepoint()
            instance = form.save(commit=False)
            instance.data_entry_staff = self.request.user
            instance.order = self.get_sales_order()
            instance.save()
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
            if cost_formset.is_valid():
                cost_formset.instance = instance
                cost_formset.save()
            else:
                transaction.savepoint_rollback(sid)
                context = {
                    'form': form,
                    'itemformset': formset,
                    'errors': ""
                }
                return self.render_to_response(context)

        return super(SalesOrderSaveMixin, self).form_valid(form)

    def formset_valid(self, instance=None, formset=None):
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
                {'slab': Slab.objects.get(id=slab).id,
                 'part_num': Slab.objects.get(id=slab).part_num,
                 'line_num': Slab.objects.get(id=slab).line_num,
                 'slablist': slab_list.id}
                for slab in new_ids
                ]
            for slab in slabs:
                slablistform = SlabListItemForm(data=slab)
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
                for id in self.get_cart().cart['current_order_slab_ids']]
            for slab in slabs:
                slablistform = SlabListItemForm(data=slab)
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


class PickupDetailView(DetailView):
    model = SalesOrderPickUp

    def get_context_data(self, **kwargs):
        item_list = self.object.items.all()
        kwargs['item_list'] = item_list
        dt = defaultdict(float)
        for item in item_list:
            dt[item.unit] += float(item.quantity)
        kwargs['item_total_quantity'] = {k: '{:.2f}'.format(v) for k, v in dt.items()}
        kwargs['item_total_count'] = len(item_list)

        cost_list = self.object.cost.all()
        kwargs['cost_list'] = cost_list
        kwargs['total_cost'] = self.object.total_cost()
        kwargs['cost_count'] = len(cost_list)
        return kwargs


class PickUpDeleteView(DeleteView):
    model = SalesOrderPickUp

    def get_success_url(self):
        self.success_url = reverse_lazy('sales:order_detail',
                                        kwargs={'pk': self.get_object().order.id})
        return self.success_url
