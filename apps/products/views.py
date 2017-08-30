from django.shortcuts import render
from django.utils.http import urlquote
from django.db.models import Count, Sum
from django.views.generic import ListView, DetailView, View
from django.views.generic import TemplateView

from .models import Product, Slab, Category, Quarry, Batch
from cart.cart import Cart

from utils import str_to_list


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        product_lst = self.model.objects.all()
        context['category_tags'] = set(item.category for item in product_lst)
        context['quarry_tags'] = set(item.quarry for item in product_lst)
        context['batch_tags'] = set(item.batch for item in product_lst)
        context['block_type_tags'] = set(
            type.get('type') for item in product_lst for type in item.get_inventory_list())
        context['choose_dict'] = self.get_GET_dict()
        return context

    def get_GET_dict(self):
        return {
            'category': self.request.GET.get('category') if self.request.GET.get('category') !='None' else None,
            'batch': self.request.GET.get('batch') if self.request.GET.get('batch') !='None' else None,
            'quarry':  self.request.GET.get('quarry') if self.request.GET.get('quarry') !='None' else None,
            'block_type': self.request.GET.get('block_type') if self.request.GET.get('block_type') !='None' else None,
        }

    def get_queryset(self):
        qs = super(ProductListView, self).get_queryset()
        GET_dict = self.get_GET_dict()
        kwargs = {}
        if GET_dict.get('category'):
            kwargs.update({'category_id': GET_dict['category']})
        if GET_dict.get('batch'):
            kwargs.update({'batch_id': GET_dict['batch']})
        if GET_dict.get('quarry'):
            kwargs.update({'quarry_id': GET_dict['quarry']})
        if kwargs:
            qs.filter(**kwargs)
        if GET_dict.get('block_type'):
            qs = [item for item in qs for type in item.get_inventory_list() if
                  type.get('type') == GET_dict.get('block_type')]
        return qs


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
        context = {}
        type = self.request.GET.get('type', None)
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

        if type and type == 'can_sell':
            if object.block_type == 'slab':
                has_booking_ids_list = [id for list in ids_list for id in list['ids'] if
                                        Slab.objects.get(id=id).has_booking]
                has_sell_ids_list = [id for list in ids_list for id in list['ids'] if
                                     Slab.objects.get(id=id).is_sell]
                context = {
                    'has_booking_ids_list': has_booking_ids_list,
                    'has_sell_ids_list': has_sell_ids_list,
                }
            elif object.block_type == 'otw':
                has_booking_ids_list = [id for list in ids_list for id in list['ids'] if
                                        Product.objects.get(block_num=id).has_booking]
                has_sell_ids_list = [id for list in ids_list for id in list['ids'] if
                                     Product.objects.get(block_num=id).has_sell]
                context = {
                    'has_booking_ids_list': has_booking_ids_list,
                    'has_sell_ids_list': has_sell_ids_list,
                }

        context.update({
            'slab_list': ids_list,
            'object': object,
            'slab_ids': cart.cart.get('slab_ids'),
            'block_type': 1 if object.block_type == 'otw' else 0
        })
        return render(request, self.template_name, context)


class OrderSlabListView(View):
    template_name = 'products/order_slab_list.html'

    def get(self, request, **kwargs):
        cart = Cart(request)
        context = {}
        type = self.request.GET.get('type', None)
        block_num = self.request.GET.get('block_num', None)
        slab_ids = self.request.GET.get('ids')
        object = Product.objects.get(block_num=block_num)
        self.object = object

        if object.block_type == 'otw':
            ids_list = object.get_block_list()
        elif object.block_type == 'slab':
            if slab_ids:
                ids_list = object.get_slab_list(slab_ids=str_to_list(slab_ids),
                                                object_format=True)
            else:
                ids_list = object.get_slab_list(object_format=True)

        if type and type == 'can_sell':
            if object.block_type == 'slab':
                has_booking_ids_list = [id for list in ids_list for id in list['ids'] if
                                        Slab.objects.get(id=id).has_booking]
                has_sell_ids_list = [id for list in ids_list for id in list['ids'] if
                                     Slab.objects.get(id=id).is_sell]
                context = {
                    'has_booking_ids_list': has_booking_ids_list,
                    'has_sell_ids_list': has_sell_ids_list,
                }
            elif object.block_type == 'otw':
                has_booking_ids_list = [id for list in ids_list for id in list['ids'] if
                                        Product.objects.get(block_num=id).has_booking]
                has_sell_ids_list = [id for list in ids_list for id in list['ids'] if
                                     Product.objects.get(block_num=id).has_sell]
                context = {
                    'has_booking_ids_list': has_booking_ids_list,
                    'has_sell_ids_list': has_sell_ids_list,
                }

        context.update({
            'slab_list': ids_list,
            'object': object,
            'slab_ids': cart.cart.get('slab_ids'),
            'block_type': 1 if object.block_type == 'otw' else 0
        })
        return render(request, self.get_template_name(), context)

    def get_template_name(self):
        if self.object.block_type == 'otw':
            return 'products/order_block_list.html'
        else:
            return self.template_name


class SearchView(TemplateView):
    template_name = 'products/search.html'

    def post(self, request, *args, **kwargs):
        object_list = Product.objects.filter(block_num__contains=self.request.POST.get('q')).all()
        return render(request, self.template_name, {'object_list': object_list})
