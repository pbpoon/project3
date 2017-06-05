from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, DeleteView, CreateView, UpdateView, View
from django.core.urlresolvers import reverse_lazy

from .models import PurchaseOrder, PurchaseOrderItem, Supplier
from .forms import purchase_form, AddExcelForm

import xlrd

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
        if self.request.method == 'POST':
            kwargs['form'] = AddExcelForm(self.request.POST, self.request.FILES)
        else:
            kwargs['form'] = AddExcelForm()
        return super(PurchaseOrderDetailView, self).get_context_data(**kwargs)


class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    fields = '__all__'
    template_name = 'purchase/purchaseorder_form.html'
    excel_form = AddExcelForm

    def get_context_data(self, **kwargs):
        if self.request.method == 'POST':
            kwargs['excel_form'] = self.excel_form(self.request.POST)
        else:
            kwargs['excel_form'] = self.excel_form()
        return super(PurchaseOrderCreateView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        context = self.get_context_data()
        context['formset'].save()
        context['form'].save()
        return super(PurchaseOrderCreateView, self).form_valid(form)


class AddExcelFileView(View):
    template_name = 'purchase/purchaseorder.html'

    def get(self, request):
        object = get_object_or_404(PurchaseOrder, pk=self.kwargs.get['order_id'])
        form = AddExcelForm()
        context = {
            'object': object,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        object = get_object_or_404(PurchaseOrder, pk=self.kwargs.get['order_id'])
        form = AddExcelForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.files.get('file')
            if f:
                data = xlrd.open_workbook(file_contents=f.read())
                # table = data.sheet_by_name(by_name)
                table = data.sheets()[0]
                nrows = table.nrows  # 总行数
                colnames = table.row_values(0)  # 表头列名称数据
                print(colnames)
                list = []
            #     # accounts = [Account(name=str(x)) for x in set(table.col_values(10, 1))]
            #     print(accounts)
            #     # Account.objects.bulk_create(accounts)
            #     for rownum in range(1, nrows):
            #         row = table.row_values(rownum)
            #         for index, i in enumerate(range(len(colnames))):
            #             if row:
            #                 if index == 4 or index == 14:
            #                     row[i] = xldate_as_datetime(row[i], 0)
            #                 elif index == 8 or index == 13 or index == 15:
            #                     row[i] = bool(row[i])
            #                 elif index == 10:
            #                     row[i] = Account.objects.get(name=str(row[i]))
            #                 else:
            #                     row[i] = str(row[i])
            #         if not People.objects.filter(first_name=row[1], last_name=row[2]):
            #             list.append(People(first_name=row[1], last_name=row[2], sex=row[3], birthday=row[4],
            #                                nationality=row[5], education=row[6], account_type=row[7], is_marry=row[8],
            #                                id_card_num=row[9], phone_num=row[12], is_getmoney=row[13], account=row[10],
            #                                join_d=row[14],
            #                                is_main=row[15]
            #                                ))
            #         print(list)
            #         # account = row[10],
            # People.objects.bulk_create(list)
            # return HttpResponse('OK')
