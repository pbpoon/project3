from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, \
    redirect
from django.views.generic import ListView, DetailView, DeleteView, CreateView, \
    UpdateView, View, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy, reverse
from django.db import transaction
from django.contrib import messages

from .models import PurchaseOrder, PurchaseOrderItem, Supplier, ImportOrderItem, \
    ImportOrder, PaymentHistory
from .forms import PurchaseOrderItemForm, ImportOrderForm, PaymentForm, \
    PurchaseOrderItemBaseInlineFormset, \
    ImportOrderItemForm
from django.forms import inlineformset_factory
from cart.cart import Cart
from process.models import TSOrderItem, KSOrderItem, MBOrderItem, STOrderItem

from utils import AddExcelForm, ImportData

import xlrd
from decimal import Decimal


class SupplierListView(ListView):
    model = Supplier
    template_name = 'purchase/supplier_list.html'


class SupplierDetailView(DetailView):
    model = Supplier
    template_name = 'purchase/supplier.html'


class SupplierCreateView(CreateView):
    model = Supplier
    fields = '__all__'
    template_name = 'purchase/supplier_form.html'


class SupplierUpdateView(UpdateView):
    model = Supplier
    fields = '__all__'
    template_name = 'purchase/supplier_form.html'


class SupplierDeleteView(DeleteView):
    model = Supplier
    success_url = reverse_lazy('purchase:supplier_list')
    # template_name_suffix = 'purchase/supplier_confirm_delete'


class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'purchase/list.html'


class PurchaseOrderDetailView(DetailView):
    model = PurchaseOrder

    def get_context_data(self, **kwargs):
        kwargs['payment_history'] = PaymentHistory.objects.filter(
            order=self.object.order)
        kwargs['block_list'] = [block.block_num for block in
                                self.object.item.all()]
        if self.request.method == 'POST':
            kwargs['form'] = AddExcelForm(self.request.POST, self.request.FILES)
        else:
            kwargs['form'] = AddExcelForm()
        return super(PurchaseOrderDetailView, self).get_context_data(**kwargs)


class ImportDataView(TemplateView):
    template_name = 'purchase/import_data.html'

    def get_context_data(self, **kwargs):
        cart = Cart(self.request)
        self.import_block_list = cart.cart.get('import_block')
        if self.request.method == 'GET':
            if self.import_block_list:
                kwargs['block_list'] = self.import_block_list
            else:
                kwargs['file_form'] = AddExcelForm()

        return super(ImportDataView, self).get_context_data(**kwargs)

    def post(self, request):
        cart = Cart(self.request)
        file_form = AddExcelForm(self.request.POST, self.request.FILES)
        clean = self.request.POST.get('clean')
        if clean:
            del cart.cart['import_block']
            cart.save()
            return redirect('purchase:import_data')
        else:
            if file_form.is_valid():
                f = file_form.files.get('file')
                importer = ImportData(f, data_type='block_list')
                cart.cart['import_block'] = importer.data
                cart.save()
                return redirect('purchase:import_data')


class PurchaseOrderEditMixin(object):
    '''
    PurchaseOrder和ImportOrder的编辑Mixin,主要生成inline formset，
    增加的数据入，
    item_model对应formset的model
    itemform_class 对应formset的form，因为这个mixin需要配合改写了__init__,save,clean等方法来配合使用
    itemform_field住要用来设定formset的fields的顺序是
    '''
    item_model = None
    itemform_class = None
    itemform_fields = None

    def get_formset(self, **kwargs):
        extra = 1
        if self.object is not None:
            extra = 0
        elif self.import_data_list:
            extra = len(self.import_data_list)
        return inlineformset_factory(self.model, self.item_model,
                                     form=self.itemform_class,
                                     formset=PurchaseOrderItemBaseInlineFormset,
                                     fields=self.itemform_fields,
                                     extra=extra, can_delete=True)

    def get_context_data(self, **kwargs):
        cart = Cart(self.request)
        self.import_data_list = cart.cart.get('import_block')
        if self.request.method == 'GET':
            kwargs['formset'] = self.get_formset()(instance=self.object)
            if self.object is None:
                if self.import_data_list:
                    for form, data in zip(kwargs['formset'],
                                          self.import_data_list):
                        data['block_name'] = data.pop('block_num')
                        form.initial.update(data)
        else:
            kwargs['formset'] = self.get_formset()(self.request.POST,
                                                   self.request.FILES)
        return super(PurchaseOrderEditMixin, self).get_context_data(**kwargs)

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        with transaction.atomic():
            sid = transaction.savepoint()
            form.instance.data_entry_staff = self.request.user
            self.object = form.save()
            formset.instance = self.object
            if formset.is_valid():
                formset.save()
                cart = Cart(self.request)
                if cart.cart.get('import_block'):
                    del cart.cart['import_block']
                transaction.on_commit(cart.save)
                messages.success(self.request, '订单提交成功！')
            else:
                transaction.savepoint_rollback(sid)
                messages.error(self.request, '订单提交失败！')
                context = {
                    'form': form,
                    'formset': formset,
                }
                return render(self.request, self.get_template_names(), context)
        return super(PurchaseOrderEditMixin, self).form_valid(form)


class PurchaseOrderCreateView(LoginRequiredMixin, PurchaseOrderEditMixin,
                              CreateView):
    model = PurchaseOrder
    fields = (
        'finish_pay', 'supplier', 'handler', 'date', 'cost_money', 'cost_by',
        'ps',
        'file')
    item_model = PurchaseOrderItem
    itemform_class = PurchaseOrderItemForm
    itemform_fields = (
        'block_name', 'category', 'quarry', 'batch', 'weight', 'long', 'width',
        'high', 'm3', 'price', 'ps')


class PurchaseOrderUpdateView(LoginRequiredMixin, PurchaseOrderEditMixin,
                              UpdateView):
    model = PurchaseOrder
    fields = (
        'finish_pay', 'supplier', 'handler', 'date', 'cost_money', 'cost_by',
        'ps', 'file'
    )
    item_model = PurchaseOrderItem
    itemform_class = PurchaseOrderItemForm
    itemform_fields = (
        'block_name', 'category', 'quarry', 'batch', 'weight', 'long', 'width',
        'high', 'm3', 'price', 'ps')


class PurchaseOrderDeleteView(DeleteView):
    model = PurchaseOrder
    success_url = 'purchase:purchase_order_list'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.check_item().get('error'):
            messages.error(request, '订单提交失败！')
            context = {
                'object': self.object,
                'errors': self.check_item().get('error_lst')
            }
            return render(request, self.get_template_names(), context)
        else:
            kk = [item.block_num for item in
                  self.object.item.all()]
            print(kk)
            success_url = self.get_success_url()
            # self.object.delete()
            map(lambda x: x.delete(), kk)
            return HttpResponseRedirect(success_url)

    def check_item(self):
        error = False
        error_lst = []
        self.object = self.get_object()
        items = [item.block_num_id for item in self.object.item.all()]
        if items:
            if TSOrderItem.objects.filter(block_num_id__in=items).exists():
                error = True

                block_num = [item.block_num.block_num for item in \
                             TSOrderItem.objects.filter(
                                 block_num_id__in=items).all()]
                error_lst.append('荒料编号：' + ', '.join(block_num) +
                                 '有运输订单记录。')
            if KSOrderItem.objects.filter(block_num_id__in=items).exists():
                error = True
                block_num = [item.block_num.block_num for item in \
                             KSOrderItem.objects.filter(
                                 block_num_id__in=items).all()]
                error_lst.append('荒料编号：' + ', '.join(block_num) + '有界石订单记录。')
            if TSOrderItem.objects.filter(block_num_id__in=items).exists():
                error = True
                block_num = [item.block_num.block_num for item in \
                             TSOrderItem.objects.filter(
                                 block_num_id__in=items).all()]
                error_lst.append('荒料编号：' + ', '.join(block_num) + '有补石订单记录。')
            if STOrderItem.objects.filter(block_num_id__in=items).exists():
                error = True
                block_num = [item.block_num.block_num for item in \
                             STOrderItem.objects.filter(
                                 block_num__in=items).all()]
                error_lst.append('荒料编号：' + ', '.join(block_num) + '有荒料到货订单记录。')
            if ImportOrderItem.objects.filter(block_num_id__in=items).exists():
                error = True
                block_num = [item.block_num.block_num for item in \
                             ImportOrderItem.objects.filter(
                                 block_num_id__in=items).all()]
                error_lst.append(
                    '荒料编号：' + ', '.join(block_num) + '有进口报关&运输订单记录。')
        if error:
            error_lst.append('订单明细的荒料中有以上记录，不能删除本订单！如需要删除本订单，请清除以上记录。')
            return {
                'error': True,
                'error_lst': error_lst,
            }
        else:
            return {
                'error': False
            }

    def get_context_data(self, **kwargs):
        kwargs['item_list'] = [i.block_num for i in self.object.item.all()]
        return super(PurchaseOrderDeleteView, self).get_context_data(**kwargs)


class ImportOrderListView(ListView):
    template_name = 'purchase/import_order_list.html'
    model = ImportOrder


class ImportOrderDetailView(DetailView):
    template_name = 'purchase/import_order.html'
    model = ImportOrder

    def get_context_data(self, **kwargs):
        block_list = self.object.item.all()
        kwargs['block_list'] = (block.block_num for block in block_list)
        kwargs['payment_history'] = PaymentHistory.objects.filter(
            order=self.object.order)
        return super(self.__class__, self).get_context_data(**kwargs)


class ImportOrderCreateView(LoginRequiredMixin, PurchaseOrderEditMixin,
                            CreateView):
    template_name = 'purchase/import_order_form.html'
    model = ImportOrder
    form_class = ImportOrderForm
    item_model = ImportOrderItem
    itemform_class = ImportOrderItemForm
    itemform_fields = (
        'block_name', 'category', 'quarry', 'batch', 'weight', 'long', 'width',
        'high', 'm3', 'ps')

    #
    # def post(self, request, *args, **kwargs):
    #     form = self.get_form()
    #     file_form = AddExcelForm(self.request.POST, self.request.FILES)
    #     if form.is_valid() and file_form.is_valid():
    #         object = form.save(commit=False)
    #         object.data_entry_staff = self.request.user
    #         block_list = []
    #         order_item = []
    #         error = []
    #         f = form.files.get('file')
    #         if f:
    #             data = xlrd.open_workbook(file_contents=f.read())
    #             table = data.sheets()[0]
    #             nrows = table.nrows  # 总行数
    #             colnames = table.row_values(0)  # 表头列名称数据
    #             for rownum in range(1, nrows):
    #                 row = table.row_values(rownum)
    #                 for index, i in enumerate(range(len(colnames))):
    #                     if row:
    #                         if index == 0:
    #                             row[i] = str(row[i])
    #                         elif index == 1 or index == 7:
    #                             row[i] = Decimal('{0:.2f}'.format(row[i]))
    #                         elif index == 5:
    #                             if row[i]:
    #                                 row[i] = Decimal('{0:.2f}'.format(row[i]))
    #                             else:
    #                                 row[i] = Decimal('{0:.2f}'.format(
    #                                     float(row[2]) * float(row[3]) * float(row[4]) * 0.000001))
    #                         elif index == 6:
    #                             row[i] = Batch.objects.filter(name=str(row[i]))[0]
    #                         else:
    #                             row[i] = int(row[i])
    #
    #                 if PurchaseOrderItem.objects.filter(block_num=row[0]):
    #                     if not ImportOrderItem.objects.filter(
    #                             block_num=PurchaseOrderItem.objects.filter(block_num=row[0])):
    #                         """
    #                         以后还有再加一个判断该编号荒料有没有到货记录。
    #                         """
    #                         block_num = PurchaseOrderItem.objects.get(block_num=row[0])
    #                         order_item.append(
    #                             ImportOrderItem(block_num=block_num, weight=row[1]))
    #                         block = Product.objects.get(block_num=block_num)
    #                         block.weight = row[1]
    #                         block_list.append(block)
    #                 else:
    #                     error.append(row[0])
    #             if len(error) != 0:
    #                 messages.error(self.request, '荒料编号:{}，已有数据，请检查清楚！'.format("，".join(error)))
    #                 context = {
    #                     'object': object,
    #                     'form': form,
    #                     'file_form': file_form,
    #                 }
    #                 return render(self.request, self.template_name, context)
    #         if self.request.POST.get('save'):
    #             object.save()
    #             for block_id, block in zip(order_item, block_list):
    #                 block_id.order = object
    #                 block_id.save()
    #                 block.save()
    #             messages.success(self.request, '数据已经成功保存!')
    #             success_url = object.get_absolute_url()
    #             return HttpResponseRedirect(success_url)
    #         messages.success(self.request, '数据已经成功保存!')
    #         context = {
    #             # 'object': object,
    #             'block_list': block_list,
    #             'form': form,
    #             'file_form': file_form,
    #             'total_weight': '{0:.2f}'.format(sum(float(i.weight) for i in block_list)),
    #             'total_count': len(block_list),
    #         }
    #         return render(self.request, self.template_name, context)


class PaymentListView(ListView):
    model = PaymentHistory
    template_name = 'purchase/payment_list.html'


class PaymentDetailView(DetailView):
    model = PaymentHistory
    template_name = 'purchase/payment.html'


class PaymentCreateView(CreateView):
    form_class = PaymentForm
    template_name = 'purchase/payment_form.html'


class PaymentUpdateView(UpdateView):
    model = PaymentHistory
    form_class = PaymentForm
    template_name = 'purchase/payment_form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.data_entry_staff = self.request.user
        instance.save()
        return super(self.__class__, self).form_valid(form)
