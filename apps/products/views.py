from django.shortcuts import render
from django.db.models import Count, Sum
from django.views.generic import ListView, DetailView, View
from .models import Product, Slab, Category, Quarry, Batch


class ProductListView(ListView):
    model = Product


class ProductDetailView(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        kwargs['slab_list'] = self.object.get_slab_list(object_format=True)
        return super(ProductDetailView, self).get_context_data(**kwargs)


class ProductSlabListView(View):
    template_name = 'product/slablist_detail.html'

    def get(self, request):
        object = Product.objects.all()
        block_num = self.kwargs.get('block_num', None)
        slab_ids = self.request.GET.get('slab_ids')
        if block_num:
            object = object.filter(block_num=block_num)
        if slab_ids:
            slab_list = object.get_slab_list(slab_ids=slab_ids, object_format=True)
        else:
            slab_list = object.get_slab_list(object_format=True)
        return render(request, self.template_name, {'slab_list': slab_list})
