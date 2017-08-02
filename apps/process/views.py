from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.forms import inlineformset_factory
from django.core.urlresolvers import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, \
    DeleteView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import ProcessOrder, ServiceProvider, TSOrderItem, MBOrderItem, \
    KSOrderItem, STOrderItem, SlabList, SlabListItem
from products.models import Product, Slab, InventoryAddress
from .forms import TSOrderItemForm, MBOrderItemForm, KSOrderItemForm, \
    STOrderItemForm, ProcessOrderForm, SlabListForm, \
    SlabListItemForm, CustomBaseInlineFormset
from products.forms import SlabModelFormset, SlabForm
from cart.cart import Cart


class SaveCurrentOrderSlabsMixin(object):
    def get_context_data(self, **kwargs):
        if self.object:
            cart = Cart(self.request)
            try:
                slab_model = ContentType.objects.get_for_model(self.object)
                slab_list = SlabList.objects.get(content_type__pk=slab_model.id,
                                                 object_id=self.object.id).item.all()
                # slab_list = self.object.slab_list.get(object_id=self.object.id).item.all()
                cart.cart['current_order_slab_ids'] = [str(item.slab.id) for item in slab_list]
            except Exception as e:
                cart.cart['current_order_slab_ids'] = []
            finally:
                cart.save()
        return super(SaveCurrentOrderSlabsMixin, self).get_context_data(**kwargs)


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


class ProcessOrderDetailView(SaveCurrentOrderSlabsMixin, DetailView):
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
        if self.object.order_type == 'MB':
            kwargs['slab_list'] = self.object.slab_list.get(object_id=self.object.id)
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
            import_list = self.get_slab_ids()
            model = MBOrderItem
            form = MBOrderItemForm
            fields = (
                'id', 'block_num', 'block_name', 'thickness', 'pic', 'quantity', 'unit', 'price',
                'date', 'ps', 'slab_list')
            extra = len(import_list)
        elif type == 'ST':
            model = STOrderItem
            form = STOrderItemForm
            fields = '__all__'
        if self.object is not None:
            extra = 0
        return inlineformset_factory(parent_model=self.model, model=model,
                                     form=form, formset=CustomBaseInlineFormset,
                                     fields=fields,
                                     extra=extra, can_delete=True)

    def get_context_data(self, **kwargs):
        """
        :param kwargs:
        errors:错误信息，主要记录新建订单录入时候的错误
        order_type:把编辑的order类型返回到template，方便提交订单时候可以根据order类型做出业务判断
        data_list:是itemformset的block_name的data_list的数据
        allow_edit: 是否为编辑状态，如果是，打开的slab_list的checkbox可以选择。
        :return:
        """
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
                # if self.object is None:
                for form, data in zip(context['itemformset'],
                                      self.get_slab_ids()):
                    try:
                        block_num = Product.objects.get(
                            block_num=data['block_num'])
                    except Exception as e:
                        error.append('导入的码单中：荒料编号[{}]不存在，请查询'.format(
                            data['block_num']))
                    else:
                        form.initial.update({
                            'block_name': data['block_num'],
                            'block_num': block_num,
                            'thickness': data['thickness'],
                            'pic': data['block_pics'],
                            'quantity': data['block_m2'],
                            'unit': 'm2',
                        })
            context['errors'] = error
            context['order_type'] = self.order_type
            context['data_list'] = self.get_block_num_datalist()
            context['allow_edit'] = True
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

    def get_slab_ids(self):
        cart = Cart(self.request)
        if self.object is None:
            return cart.make_import_slab_list()
        return cart.make_slab_list(key='current_order_slab_ids')

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

    def get_initial(self):
        if self.object is None:
            return {'data_entry_staff': self.request.user}
        return super(OrderFormsetMixin, self).get_initial()

    def form_valid(self, form):
        data = self.get_context_data()
        formset = data['itemformset']
        cart = Cart(self.request)
        with transaction.atomic():
            sid = transaction.savepoint()
            instance = form.save()
            if formset.is_valid():
                formset.instance = instance
                items = formset.save()
                for item in items:
                    if self.order_type == 'TS':
                        address = item.destination
                    else:
                        address = instance.service_provider
                    InventoryAddress._save(order=instance, block_num=item.block_num,
                                           address=address)
                if self.order_type == 'MB':
                    try:
                        """
                        尝试获取slab_list
                        如果没有就新建一个slab_list
                        """
                        slab_model = ContentType.objects.get_for_model(instance)
                        slab_list = SlabList.objects.get(content_type__pk=slab_model.id,
                                                         object_id=instance.id)
                    except Exception as e:
                        slab_list = SlabList.objects.create(order=instance,
                                                            data_entry_staff_id=self.request.user.id)
                    finally:
                        """
                        把slab_list包含的slab id 读取出来，和选择的slab id作比较
                        如果是新订单就把import_slab_list用get_import_slab_list_by_parameter遍历出来添加到列表，
                        如果是编辑订单就直接读取cart的current_order_slab_ids，并用make_slab_list返回码单
                        """
                        slabs = []
                        if self.object is None:
                            for i in items:
                                slabs.extend(
                                    cart.get_import_slab_list_by_parameter(i.block_num,
                                                                           i.thickness))
                        else:
                            slabs = cart.cart['current_order_slab_ids']
                        errors = []
                        if self.object is not None:
                            """
                            如果是编辑订单状态就把新选择的ids和订单保存的ids做比较
                            old_ids 是本订单保存的slab_id
                            new_ids 是用修改过的（cart['current_order_slab_ids']与old_ids差集
                            del_ids 是上行的反转差集
                            """
                            old_ids = [str(item.id) for item in slab_list.item.all()]
                            new_ids = set(slabs) - set(old_ids)
                            del_ids = set(old_ids) - set(slabs)
                            if new_ids:
                                for id in new_ids:
                                    slab = Slab.objects.get(pk=id)
                                    SlabListItem.objects.create(slab_list=slab_list,
                                                                slab=slab,
                                                                part_num=slab.part_num,
                                                                line_num=slab.line_num)
                            for id in del_ids:
                                """删除之前有记录，但修改后没有选择的数据"""
                                slab = SlabListItem.objects.get(slab_id=id)
                                slab.delete()
                        else:
                            for data in slabs:
                                # if data['id'] not in old_slab_list_ids:
                                data['block_num'] = Product.objects.get(
                                    block_num=data['block_num']).id
                                slabform = SlabForm(data=data)
                                if slabform.is_valid():
                                    slab = slabform.save()
                                    slab_list_item_data = {'slab': slab.id,
                                                           'slablist': slab_list.id,
                                                           'part_num': slab.part_num,
                                                           'line_num':
                                                               slab.line_num}
                                    slab_list_item_form = SlabListItemForm(
                                        data=slab_list_item_data)

                                    if slab_list_item_form.is_valid():
                                        slab_list_item_form.save()
                                    else:
                                        errors.append(slabform.errors)
                                else:
                                    errors.append(slabform.errors)
                        if errors:
                            transaction.savepoint_rollback(sid)
                            context = {
                                'order_type': self.get_order_type(),
                                'form': form,
                                'itemformset': formset,
                                'data_list': self.get_block_num_datalist(),
                                'errors': errors
                            }
                            return self.render_to_response(context)

            else:
                transaction.savepoint_rollback(sid)
                context = {
                    'order_type': self.get_order_type(),
                    'form': form,
                    'itemformset': formset,
                    'data_list': self.get_block_num_datalist()
                }
                return self.render_to_response(context)

                # success_url = 'process:order_list'
                # return redirect(success_url)
            return super(OrderFormsetMixin, self).form_valid(form)


class ProcessOrderCreateView(LoginRequiredMixin, OrderFormsetMixin, CreateView):
    model = ProcessOrder
    form_class = ProcessOrderForm


class ProcessOrderUpdateView(LoginRequiredMixin, OrderFormsetMixin, UpdateView):
    model = ProcessOrder
    form_class = ProcessOrderForm
