from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import CustomerInfo, Province, City
from .forms import SalesOrderForm

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


class CustomerInfoCreateView(LoginRequiredMixin, ProvinceCityInfoMixin, CreateView):
    model = CustomerInfo
    form_class = SalesOrderForm
    # fields = '__all__'


class CustomerInfoUpdateView(LoginRequiredMixin, ProvinceCityInfoMixin, UpdateView):
    model = CustomerInfo
    fields = '__all__'


class CustomerInfoDeleteView(LoginRequiredMixin, DeleteView):
    model = CustomerInfo


class ImportView(FormView):
    template_name = 'sales/customerinfo_form.html'
    form_class = AddExcelForm

    def form_valid(self, form):
        f = form.files.get('file')
        import_data = ImportData(f, data_type='city').data
        for i in import_data:
            City.objects.create(**i)
        return HttpResponse('0k')


def get_city_info(request):
    province_id = request.GET.get('province_id')
    father_id = Province.objects.get(pk=province_id).province_id
    citys = City.objects.filter(father_id=father_id).all()
    city_lst = [{'city_id': city.id, 'city_name': city.name} for city in citys]
    print(city_lst)
    return JsonResponse(city_lst, safe=False)
