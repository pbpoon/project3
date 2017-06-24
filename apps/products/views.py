from django.shortcuts import render
from django.db.models import Count, Sum
from django.views.generic import ListView, DetailView
from .models import Product, Slab, Category, Quarry, Batch


class ProductListView(ListView):
    model = Product


class ProductDetailView(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        kwargs['slab_list'] = self.object.get_slab_list()
        return super(ProductDetailView, self).get_context_data(**kwargs)

