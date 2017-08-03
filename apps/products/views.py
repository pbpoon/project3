from django.shortcuts import render
from django.db.models import Count, Sum
from django.views.generic import ListView, DetailView, View
from django.views.generic import TemplateView

from .models import Product, Slab, Category, Quarry, Batch
from cart.cart import Cart

from utils import str_to_list


class ProductListView(ListView):
    model = Product


class ProductDetailView(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        kwargs['inventory_list'] = self.object.get_inventory_list()
        kwargs['business_list'] = self.object.get_business()
        return super(ProductDetailView, self).get_context_data(**kwargs)


class ProductSlabListView(View):
    template_name = 'products/slab_list.html'

    def get(self, request, **kwargs):
        cart = Cart(request)
        block_num = self.kwargs.get('block_num', None)
        slab_ids = self.request.GET.get('slab_ids')
        object = Product.objects.get(block_num=block_num)
        if object.block_type == 'otw':
            ids_list = object.get_block_list()
        elif object.block_type == 'slab':
            if slab_ids:
                ids_list = object.get_slab_list(slab_ids=str_to_list(slab_ids),
                                                object_format=True)
            else:
                ids_list = object.get_slab_list(object_format=True)

        context = {
            'slab_list': ids_list,
            'object': object,
            'slab_ids': cart.cart.get('slab_ids'),
            'block_type': 1 if object.block_type == 'otw' else 0
        }
        return render(request, self.template_name, context)


class OrderSlabListView(View):
    template_name = 'products/order_slab_list.html'

    def get(self, request, **kwargs):
        cart = Cart(request)
        block_num = self.request.GET.get('block_num', None)
        slab_ids = self.request.GET.get('slab_ids')
        object = Product.objects.get(block_num=block_num)
        if object.block_type == 'otw':
            ids_list = object.get_block_list()
        elif object.block_type == 'slab':
            if slab_ids:
                ids_list = object.get_slab_list(slab_ids=str_to_list(slab_ids),
                                                object_format=True)
            else:
                ids_list = object.get_slab_list(object_format=True)

        context = {
            'slab_list': ids_list,
            'object': object,
            'slab_ids': cart.cart.get('slab_ids'),
            'block_type': 1 if object.block_type == 'otw' else 0
        }
        return render(request, self.template_name, context)

    # def get(self, request, **kwargs):
    #     cart = Cart(request)
    #     object = Product.objects.all()
    #     block_num = self.request.GET.get('block_num', None)
    #     thickness = self.request.GET.get('thickness', None)
    #     try:
    #         block_num_id = Product.objects.get(block_num=block_num).id
    #     except:
    #         pass
    #     if block_num_id:
    #         ids = [item.id for item in Slab.objects.filter(block_num_id=block_num_id,
    #                                                        thickness=thickness).all()]
    #     slab_ids = cart.cart['current_order_slab_ids']
    #
    #     if block_num:
    #         object = object.filter(block_num=block_num).all()[0]
    #     if ids:
    #         slab_list = object.get_slab_list(slab_ids=ids,
    #                                          object_format=True)
    #     else:
    #         slab_list = object.get_slab_list(object_format=True)
    #     context = {
    #         'slab_list': slab_list,
    #         'object': object,
    #         'slab_ids': slab_ids,
    #     }
    #     return render(request, self.template_name, context)


class SearchView(TemplateView):
    template_name = 'products/search.html'

    def post(self, request, *args, **kwargs):
        object_list = Product.objects.filter(block_num__contains=self.request.POST.get('q')).all()
        return render(request, self.template_name, {'object_list': object_list})
