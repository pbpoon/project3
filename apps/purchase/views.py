from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, DeleteView, CreateView, UpdateView, View, FormView
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from .models import PurchaseOrder, PurchaseOrderItem, Supplier
from .forms import purchase_form, AddExcelForm
from products.models import Product, Batch
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


class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    fields = ['supplier', 'handler' ]
    template_name = 'purchase/purchaseorder_form.html'
    excel_form = AddExcelForm

    def get_context_data(self, **kwargs):
        if self.request.method == 'POST':
            kwargs['excel_form'] = self.excel_form(self.request.POST)
        else:
            kwargs['excel_form'] = self.excel_form()
        return super(PurchaseOrderCreateView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.data_entry_staff = self.request.user
        instance.save()
        return super(PurchaseOrderCreateView, self).form_valid(form)


class AddExcelFileView(FormView):
    template_name = 'purchase/purchaseorder.html'
    form_class = AddExcelForm

    def dispatch(self, request, *args, **kwargs):
        order_id = self.request.GET.get('order_id')
        self.object = None
        if order_id:
            self.object = get_object_or_404(PurchaseOrder, pk=order_id)
        return super(AddExcelFileView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        block_lst = []
        order_item = []
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
                        elif index == 6:
                            row[i] = Batch.objects.filter(name=str(row[i]))[0]
                        elif index == 1 or index == 5:
                            row[i] = Decimal(row[i]).quantize(Decimal(0.00))
                        else:
                            row[i] = Decimal(row[i]).quantize(Decimal(0))
                if not PurchaseOrderItem.objects.filter(block_num=row[0]) and Product.objects.get(block_num=row[0],
                                                                                                  batch=row[6]):
                    order_item.append(PurchaseOrderItem(block_num=row[0]))
                    block_lst.append(
                        Product(weight=row[1], long=row[2], width=row[4], high=row[4], m3=row[5], batch=row[6]))
                else:
                    messages.error(self.request, '荒料编号[{}]已经存在数据中，请检查清楚！'.format(row[0]))
                    context ={
                        'object':self.object,
                        'form': form,
                    }
                    return render(self.request, self.template_name, context)

        block_list = []
        for block_id, block in zip(order_item, block_lst):
            block_id.order = self.object
            block_id.save()
            block.block_num = block_id
            block.save()
            block_list.append(block)
        messages.success(self.request, '数据已经成功导入!')
        context = {
            'object': self.object,
            'block_list': block_list,
        }
        return render(self.request, self.template_name, context)
        # def post(self, request):
        #     save = self.request.GET.get('save')
        #     form = AddExcelForm(request.POST, request.FILES)
        #     block_lst = []
        #     order_item = []
        #     if form.is_valid():
        #         f = form.files.get('file')
        #         if f:
        #             data = xlrd.open_workbook(file_contents=f.read())
        #             # table = data.sheet_by_name(by_name)
        #             table = data.sheets()[0]
        #             nrows = table.nrows  # 总行数
        #             colnames = table.row_values(0)  # 表头列名称数据
        #             print(colnames)
        #
        #             #     # accounts = [Account(name=str(x)) for x in set(table.col_values(10, 1))]
        #             #     print(accounts)
        #             #     # Account.objects.bulk_create(accounts)
        #             for rownum in range(1, nrows):
        #                 row = table.row_values(rownum)
        #                 for index, i in enumerate(range(len(colnames))):
        #                     if row:
        #                         if index == 0:
        #                             row[i] = str(row[i])
        #                         elif index == 6:
        #                             row[i] = Batch.objects.get(name=str(row[i]))
        #                         elif index == 1 or index == 5:
        #                             row[i] = Decimal(row[i]).quantize(Decimal(0.00))
        #                         else:
        #                             row[i] = Decimal(row[i]).quantize(Decimal(0))
        #                 if not PurchaseOrderItem.objects.filter(block_num=row[0]):
        #                     if not Product.objects.filter(block_num=row[0]):
        #                         order_item.append(
        #                             PurchaseOrderItem(block_num=row[0]))
        #                         block_lst.append(
        #                             Product(weight=row[1], long=row[2], width=row[4], high=row[4],
        #                                     m3=row[5], batch=row[6]))
        #     block_list = []
        #     if save:
        #         pass
        #     for block_id, block in zip(order_item, block_lst):
        #         block_id.order = self.object
        #         block_id.save()
        #         block.block_num = block_id
        #         block.save()
        #         block_list.append(block)
        #     context = {
        #         'object': self.object,
        #         'block_list': block_list,
        #     }
        #     return render(request, self.template_name, context)
