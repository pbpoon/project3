from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import ListView, DetailView, DeleteView, CreateView, UpdateView, View, FormView
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib import messages
from django.forms.models import inlineformset_factory

from .models import PurchaseOrder, PurchaseOrderItem, Supplier, ImportOrderItem, ImportOrder
from .forms import purchase_form, AddExcelForm, PurchaseOrderForm, ImportOrderForm
from products.models import Product, Batch

import xlrd
from decimal import Decimal

from datatableview.views import DatatableMixin, DatatableView


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
    template_name = 'purchase/purchaseorder_list.html'


class PurchaseOrderDetailView(DetailView):
    model = PurchaseOrder
    template_name = 'purchase/purchaseorder.html'

    def get_context_data(self, **kwargs):
        kwargs['block_list'] = [block.block for block in self.object.item.all()]
        if self.request.method == 'POST':
            kwargs['form'] = AddExcelForm(self.request.POST, self.request.FILES)
        else:
            kwargs['form'] = AddExcelForm()
        return super(PurchaseOrderDetailView, self).get_context_data(**kwargs)


class PurchaseOrderCreateView(FormView):
    template_name = 'purchase/purchaseorder_form.html'
    form_class = PurchaseOrderForm

    def get_context_data(self, **kwargs):
        if self.request.method == 'GET':
            kwargs['file_form'] = AddExcelForm()
        return super(self.__class__, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        file_form = AddExcelForm(self.request.POST, self.request.FILES)
        if form.is_valid() and file_form.is_valid():
            object = form.save(commit=False)
            object.data_entry_staff = self.request.user
            block_lst = []
            order_item = []
            error = []
            f = form.files.get('file')
            if f:
                data = xlrd.open_workbook(file_contents=f.read())
                table = data.sheets()[0]
                nrows = table.nrows  # 总行数
                colnames = table.row_values(0)  # 表头列名称数据
                for rownum in range(1, nrows):
                    row = table.row_values(rownum)
                    for index, i in enumerate(range(len(colnames))):
                        if row:
                            if index == 0:
                                row[i] = str(row[i])
                            elif index == 1 or index == 7:
                                row[i] = Decimal('{0:.2f}'.format(row[i]))
                            elif index == 5:
                                if row[i]:
                                    row[i] = Decimal('{0:.2f}'.format(row[i]))
                                else:
                                    row[i] = Decimal('{0:.2f}'.format(
                                        float(row[2]) * float(row[3]) * float(row[4]) * 0.000001))
                            elif index == 6:
                                row[i] = Batch.objects.filter(name=str(row[i]))[0]
                            else:
                                row[i] = int(row[i])
                    if not Product.objects.filter(block_num=row[0], batch=row[6]):
                        order_item.append(PurchaseOrderItem(block_num=row[0]))
                        block_lst.append(
                            Product(weight=row[1], long=row[2], width=row[4], high=row[4], m3=row[5], batch=row[6],
                                    price=row[7]))
                    else:
                        error.append(row[0])
                if len(error) != 0:
                    messages.error(self.request, '荒料编号:{}，已有数据，请检查清楚！'.format("，".join(error)))
                    context = {
                        'object': object,
                        'form': form,
                        'file_form': file_form,
                    }
                    return render(self.request, self.template_name, context)
            if self.request.POST.get('save'):
                object.save()
            block_list = []
            for block_id, block in zip(order_item, block_lst):
                block_id.order = object
                if self.request.POST.get('save'):
                    block_id.save()
                block.block_num = block_id
                if self.request.POST.get('save'):
                    block.save()
                block_list.append(block)
            messages.success(self.request, '数据已经成功导入!')
            if self.request.POST.get('save'):
                success_url = object.get_absolute_url()
                return HttpResponseRedirect(success_url)
            context = {
                # 'object': object,
                'block_list': block_list,
                'form': form,
                'file_form': file_form,
                'total_weight': '{0:.2f}'.format(sum(float(i.weight) for i in block_list)),
                'total_count': len(block_list),
            }
            return render(self.request, self.template_name, context)


class ImportOrderListView(ListView):
    template_name = 'purchase/import_order_list.html'
    model = ImportOrder


class ImportOrderDetailView(DetailView):
    template_name = 'purchase/import_order.html'
    model = ImportOrder


class ImportOrderCreateView(FormView):
    template_name = 'purchase/import_order_form.html'
    form_class = ImportOrderForm

    def get_context_data(self, **kwargs):
        if self.request.method == 'GET':
            kwargs['file_form'] = AddExcelForm()
        return super(ImportOrderCreateView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        file_form = AddExcelForm(self.request.POST, self.request.FILES)
        if form.is_valid() and file_form.is_valid():
            object = form.save(commit=False)
            object.data_entry_staff = self.request.user
            block_lst = []
            order_item = []
            error = []
            f = form.files.get('file')
            if f:
                data = xlrd.open_workbook(file_contents=f.read())
                table = data.sheets()[0]
                nrows = table.nrows  # 总行数
                colnames = table.row_values(0)  # 表头列名称数据
                for rownum in range(1, nrows):
                    row = table.row_values(rownum)
                    for index, i in enumerate(range(len(colnames))):
                        if row:
                            if index == 0:
                                row[i] = str(row[i])
                            elif index == 1 or index == 7:
                                row[i] = Decimal('{0:.2f}'.format(row[i]))
                            elif index == 5:
                                if row[i]:
                                    row[i] = Decimal('{0:.2f}'.format(row[i]))
                                else:
                                    row[i] = Decimal('{0:.2f}'.format(
                                        float(row[2]) * float(row[3]) * float(row[4]) * 0.000001))
                            elif index == 6:
                                row[i] = Batch.objects.filter(name=str(row[i]))[0]
                            else:
                                row[i] = int(row[i])

                    if PurchaseOrderItem.objects.filter(block_num=row[0]):
                        if not ImportOrderItem.objects.filter(block_num_id=Product.objects.filter(block_num=row[0])):
                            """
                            以后还有再加一个判断该编号荒料有没有到货记录。
                            """
                            order_item.append(ImportOrderItem(block_num_id=Product.objects.filter(block_num=row[0]), weight=row[1]))
                            block_lst.append(
                                Product(weight=row[1], long=row[2], width=row[4], high=row[4], m3=row[5], batch=row[6],
                                        price=row[7]))


                    else:
                        error.append(row[0])
                if len(error) != 0:
                    messages.error(self.request, '荒料编号:{}，已有数据，请检查清楚！'.format("，".join(error)))
                    context = {
                        'object': object,
                        'form': form,
                        'file_form': file_form,
                    }
                    return render(self.request, self.template_name, context)
            if self.request.POST.get('save'):
                object.save()
            block_list = []
            for block_id, block in zip(order_item, block_lst):
                block_id.order = object
                if self.request.POST.get('save'):
                    block_id.save()
                # block_id.block_num = block_id
                if self.request.POST.get('save'):
                    block.save()
                block_list.append(block)
            messages.success(self.request, '数据已经成功导入!')
            if self.request.POST.get('save'):
                success_url = object.get_absolute_url()
                return HttpResponseRedirect(success_url)
            context = {
                # 'object': object,
                'block_list': block_list,
                'form': form,
                'file_form': file_form,
                'total_weight': '{0:.2f}'.format(sum(float(i.weight) for i in block_list)),
                'total_count': len(block_list),
            }
            return render(self.request, self.template_name, context)
