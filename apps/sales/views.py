from collections import defaultdict
from datetime import date, datetime
from django.db.models import Q

from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from django.views import View
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
    SalesOrderPickUpItem, SalesOrderPickUpCost, ProceedsAccount, SalesProceeds, OrderExtraCost
from .forms import SalesOrderForm, CustomerInfoForm, SalesOrderItemForm, OrderPriceForm, \
    PickUpItemForm
from django.forms import inlineformset_factory, formset_factory, modelformset_factory

from utils import AddExcelForm, ImportData, item2sales
from decimal import Decimal


class GetAnotherOrderMixin(object):
    def get_another_order(self):
        try:
            another_order = SalesOrder.objects.get(pk=self.kwargs.get('another_order'))
            return another_order
        except Exception as e:
            raise ValueError('没有输入正确的order')


class LimitsMixin(object):
    def get_context_data(self, **kwargs):
        self.order = self.get_order()
        type = self.order.status
        is_proceeds = self.order.is_proceeds
        limits = {
            'pickup': False if type in 'CF' else True,
            'is_proceeds': True if type in 'V' and not self.order.is_proceeds else False,
            'proceeds': False if type in 'CF' else True,
            'edit': True if type in 'NM' else False,
            'close': False if type in 'CF' else True,
            'verify': True if type in 'NM' else False,
            'cancel': True if type == 'V' else False,
            'finish': True if type == 'V' and is_proceeds else False,
        }
        kwargs['limits'] = limits
        return kwargs


class PickUpOrderInfoMixin(GetAnotherOrderMixin):
    def get_order_item_can_pickup_ids(self):
        slab_ids = []
        block_ids = []
        for slab_list in self.get_another_order().slab_list.all():
            for slab in slab_list.item.all():
                if not slab.slab.has_pickup:
                    slab_ids.append(str(slab.slab.id))

        for item in self.get_another_order().items.all():
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
            return self._get_cost_formset_class()(data=self.request.GET, prefix='cost_fs',
                                                  instance=self.object)

        else:
            if self.request.method in ('POST', 'PUT'):
                return self._get_cost_formset_class()(data=self.request.POST, prefix='cost_fs',
                                                      instance=self.object)

            return self._get_cost_formset_class()(instance=self.object, prefix='cost_fs')


class VerifyMixin(LimitsMixin):
    model = None

    def get_context_data(self, **kwargs):
        self.order = self.get_order()
        if self.order.status not in 'CF':
            if self.order.finish:
                self.order.status = 'F'
                self.order.save()
        is_proceeds = self.request.GET.get('is_proceeds')
        if is_proceeds is not None:
            extra_info = {
                'show': True,
                'info': f'本单还有余款：￥{ self.get_order().balance }未收。 是否确认完成收款？',
                'done_button_name': 'is_proceeds',
            }
            kwargs['extra_info'] = extra_info
        return super(VerifyMixin, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.order = self.get_order()
        self.path = request.META.get('HTTP_REFERER')
        self.type = self.get_operation_type()
        if self.check_status():
            self._process_type(self.type)  # 以不同的状态处理
        else:
            messages.error(request, '该订单不能通过审核!')
        return redirect(self.path)

    def _process_type(self, type):
        if type is not None:
            return getattr(self, f'process_{type}')()
        self.path = reverse('sales:order_detail', kwargs={'pk': self.order.id})

    def process_verify(self):
        is_sell = []
        for list in self.order.slab_list.all():
            issell = set(item.slab.block_num.block_num for item in list.item.all() \
                         if item.slab.is_sell or item.slab.has_booking)
            is_sell.extend(issell)
        for item in self.order.items.all():
            if item.thickness == '荒料':
                if Product.objects.get(block_num=item.block_num).sale.exclude(
                        order__status='C').exclude(order__order=self.order.order).exists():
                    is_sell.append(str(item.block_num))
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
        self.order.is_proceeds = False
        self.order.verifier = None
        self.order.verify_date = None
        self.order.save()

    def process_close(self):
        if not self.order.pickup.exists():
            for list in self.order.slab_list.all():
                for item in list.item.all():
                    slab = item.slab
                    slab.is_sell = False
                    slab.is_booking = False
                    slab.save()
            self.order.status = 'C'
            self.order.save()
            messages.success(self.request, '该订单已关闭！')
        else:
            pickup_count = self.order.pickup.all().count()
            messages.error(self.request, f'该订单已有提货记录{pickup_count}条，不能关闭订单。如果真要关闭，请删除记录！')

    def process_is_proceeds(self):
        if self.request.POST.get('is_proceeds'):
            self.order.is_proceeds = True
            self.order.save()
            messages.success(self.request, '本单已完成收款!')
        self.path = reverse('sales:order_detail', kwargs={'pk': self.order.id})

    def check_status(self):
        if self.type == 'verify':
            allow = 'NM'
        elif self.type == 'close' or self.type == 'is_proceeds':
            allow = 'NVM'
        elif self.type == 'finish':
            allow = 'V'
        elif self.type == 'cancel':
            allow = 'V'
        else:
            allow = 'NVMFC'
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
        elif p.get('is_proceeds'):
            type = 'is_proceeds'
        else:
            type = None
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
        context = super(SalesOrderDetailView, self).get_context_data(**kwargs)
        cart = Cart(self.request)
        can_pickup_ids = self.get_order_item_can_pickup_ids()
        cart.cart['can_pickup_block_ids'], \
        cart.cart['can_pickup_slab_ids'] = can_pickup_ids['block_ids'], can_pickup_ids['slab_ids']
        cart.cart['first_status'] = [1]  # 下标志
        cart.save()

        # 订单货品信息
        item_list = self.object.items.all()
        items = self.get_cart().make_items_list(key='current_order')
        context['item_list'] = zip(item_list, items)
        context['total_count'] = self.object.items.all().count()
        context['total_pic'] = sum(int(item.pic) for item in item_list)
        context['total_part'] = sum(int(item.part) for item in item_list if item.part)
        item_dt = defaultdict(float)
        for item in item_list:
            item_dt[item.unit] += float(item.quantity)
        context['total_quantity'] = {k: '{:.2f}'.format(v) for k, v in item_dt.items()}
        context['already_pickup_list'] = self.object.pickup.all()

        # 可提货相关
        if can_pickup_ids:
            can_pickup_item_list = cart.make_items_list(key='can_pickup')
            context['can_pickup_item_list'] = can_pickup_item_list
            can_pickup_dt = defaultdict(float)
            for item in can_pickup_item_list:
                can_pickup_dt[item['unit']] += float(item['quantity'])
            context['can_pickup_total_quantity'] = {k: '{:.2f}'.format(v) for k, v in
                                                    can_pickup_dt.items()}
            context['can_pickup_total_count'] = len(can_pickup_item_list)
            context['can_pickup_total_part'] = sum(
                int(item['part_count']) for item in can_pickup_item_list if item['part_count'])
            context['can_pickup_total_pic'] = sum(
                int(item['block_pics']) for item in can_pickup_item_list)

        # 收款相关
        context['proceeds_list'] = self.object.proceeds.all()

        # 额外成本
        context['extra_cost_list'] = self.object.extra_cost.all()

        return context

    def get_another_order(self):
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
        # extra = 0
        extra = 0 if self.object else \
            len(self.get_formset_kwargs())
        return inlineformset_factory(self.model, self.formset_model, form=self.formset_class,
                                     extra=extra, fields=self._get_formset_fields(),
                                     can_delete=True)

    def get_formset_kwargs(self):
        return self.get_cart().make_items_list(key='current_order') if self.object else \
            self.get_cart().make_items_list()

    def get_formset(self):
        if self.request.GET.get('next') or self.request.method in ('POST', 'PUT'):
            return self.instance_formset()

        return self.make_formset_initial(self.instance_formset())

    def instance_formset(self):
        if self.request.GET.get('next'):
            return self._get_formset_class()(data=self.request.GET,
                                             prefix=self._get_formset_prefix(),
                                             instance=self.object)
        else:
            if self.request.method in ('POST', 'PUT'):
                return self._get_formset_class()(data=self.request.POST,
                                                 prefix=self._get_formset_prefix(),
                                                 instance=self.object)
            return self._get_formset_class()(instance=self.object,
                                             prefix=self._get_formset_prefix())

    def get_formset_data(self):
        data = self.get_cart().make_items_list(key='current_order') if self.object else \
            self.get_cart().make_items_list()
        prefix = self._get_formset_prefix()
        # forms_count = int(self.request.POST.get(f'{prefix}-TOTAL_FORMS'))
        # if self.formset_fields == '__all__':
        #     fields =[f.name for f in self.formset_model._meta.get_fields()]
        # else:
        #     fields = self._get_formset_fields()
        # data_dict ={}
        # if forms_count != len(data):
        #     prefix_num = range(len(data), forms_count)
        #     for num in prefix_num:
        #         for field in fields:
        #             _dict = {f'{prefix}-{num}-{field}': 0, f'{prefix}-{num}-DELETE': 'on', }
        #             data_dict.update(_dict)
        post_data = self.request.POST.copy()
        post_data.update({f'{prefix}-TOTAL_FORMS': len(data)})
        print(post_data)
        return post_data
        # forms_info = {f'{prefix}_TOTAL_FORMS': len(data),, }

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
            instance = form.save(commit=False)
            instance.data_entry_staff = self.request.user
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
        button_show = {
            'next': False,
            'submit': True,
        }
        kwargs['button_show'] = button_show
        return super(SalesOrderUpdateItemView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        formset = self.get_formset()
        formset.instance = self.object
        if formset.is_valid():
            formset_error = self.formset_valid(self.object, formset)
            if formset_error:
                context = {
                    'itemformset': formset,
                    'errors': formset_error['errors']
                }
                return self.render_to_response(context)
            return HttpResponseRedirect(self.object.get_absolute_url())

            # 6228 4800 7816 7777 370 中国农行厦门吾村
            # def get_formset(self):
            #     formset = self.get_formset_class()
            #     formset()
            #     return formset
            #
            #
            #
            # def get_formset_class(self):
            #     return modelformset_factory(self.formset_model, self.formset_class, fields=self.formset_fields,extra=0)


class SalesOrderCreateView(LoginRequiredMixin, SalesOrderEditMixin, SalesOrderSaveMixin,
                           CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    formset_class = SalesOrderItemForm
    formset_model = SalesOrderItem

    def get_context_data(self, **kwargs):
        price_formset = self.get_formset()
        step = self.request.GET.get('step') or self.request.POST.get('step')
        kwargs['customer_list'] = CustomerInfo.objects.all()
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
            kwargs['button_show'] = {
                'next': True,
            }
        elif step == '1':
            kwargs['step'] = '2'
            cd = price_formset.cleaned_data
            kwargs['amount'] = '{:.0f}'.format(
                sum(item['quantity'] * item['price'] for item in cd))
            kwargs['button_show'] = {
                'submit': True,
            }
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
            instance.order = self.get_another_order()
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


class PickupDetailView(SaveCurrentOrderSlabsMixin, DetailView):
    model = SalesOrderPickUp

    def get_context_data(self, **kwargs):
        context = super(PickupDetailView, self).get_context_data(**kwargs)
        cart = Cart(self.request)
        item_list = self.object.items.all()
        item_ids = cart.make_items_list(key='current_order')
        context['item_list'] = zip(item_list, item_ids)
        dt = defaultdict(float)
        for item in item_list:
            dt[item.unit] += float(item.quantity)
        context['item_total_quantity'] = {k: '{:.2f}'.format(v) for k, v in dt.items()}
        context['item_total_count'] = len(item_list)

        cost_list = self.object.cost.all()
        context['cost_list'] = cost_list
        context['total_cost'] = self.object.total_cost()
        context['cost_count'] = len(cost_list)
        return context


class PickUpDeleteView(DeleteView):
    model = SalesOrderPickUp

    def get_success_url(self):
        self.success_url = reverse_lazy('sales:order_detail',
                                        kwargs={'pk': self.get_object().order.id})
        return self.success_url


class ProceedsAccountListView(ListView):
    model = ProceedsAccount


class ProceedsAccountDetailView(DetailView):
    model = ProceedsAccount


class ProceedsAccountCreateView(CreateView):
    model = ProceedsAccount
    fields = '__all__'
    template_name = 'sales/customerinfo_form.html'


class ProceedsAccountUpdateView(UpdateView):
    model = ProceedsAccount
    fields = '__all__'
    template_name = 'sales/customerinfo_form.html'


class SalesProceedsListView(ListView):
    model = SalesProceeds


class SalesProceedsDetailView(GetAnotherOrderMixin, DetailView):
    model = SalesProceeds

    def get_context_data(self, **kwargs):
        context = super(SalesProceedsDetailView, self).get_context_data(**kwargs)
        context['order'] = self.object.order
        return context


class OrderExtraEditMixin(GetAnotherOrderMixin):
    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.data_entry_staff = self.request.user
        instance.order = self.get_another_order()
        instance.save()
        return super(OrderExtraEditMixin, self).form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['order'] = self.get_another_order()
        return super(OrderExtraEditMixin, self).get_context_data(**kwargs)


class SalesProceedsCreateView(OrderExtraEditMixin, CreateView):
    model = SalesProceeds
    fields = ('amount', 'date', 'account', 'method', 'type', 'ps')


class SalesProceedsDeleteView(GetAnotherOrderMixin, DeleteView):
    model = SalesProceeds

    def get_success_url(self):
        return reverse_lazy('sales:order_detail', kwargs={'pk': self.object.order.id})


class CheckIsProceedsAjaxView(View):
    def post(self, request, *args, **kwargs):
        if request.POST.get('is_proceeds'):
            print('OK')
            return JsonResponse('ok')
        else:
            return JsonResponse('ko')


class SalesOrderExtraCostDetailView(DetailView):
    model = OrderExtraCost


class SalesOrderExtraCostCreateView(OrderExtraEditMixin, CreateView):
    model = OrderExtraCost
    template_name = 'sales/salesproceeds_form.html'
    fields = ('date', 'item', 'desc', 'amount', 'handler')


class SalesOrderExtraCostUpdateView(OrderExtraEditMixin, UpdateView):
    model = OrderExtraCost
    template_name = 'sales/salesproceeds_form.html'
    fields = ('date', 'item', 'desc', 'amount', 'handler')


class SalesOrderExtraCostDeleteView(DeleteView):
    model = OrderExtraCost
    template_name = 'sales/salesproceeds_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('sales:order_detail', kwargs={'pk': self.object.order.id})