from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import ProcessOrder, ServiceProvider


class ServiceProviderListView(ListView):
    model = ServiceProvider


class ServiceProviderDetailView(DetailView):
    model = ServiceProvider


class ServiceProviderCreateView(CreateView):
    model = ServiceProvider


class ServiceProviderUpdateView(UpdateView):
    model = ServiceProvider


class ServiceProviderDeleteView(DeleteView):
    model = ServiceProvider
    success_url = reverse_lazy('process:serviceprovider_list')
