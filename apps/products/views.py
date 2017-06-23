from django.shortcuts import render
from django.db.models import Count, Sum
from django.views.generic import ListView, DetailView
from .models import Product, Slab, Category, Quarry, Batch


class ProductListView(ListView):
    model = Product


class ProductDetailView(DetailView):
    model = Product

    def get_context_data(self, **kwargs):
        # slab_list = Slab.objects.values('thickness').annotate(pics=Count('id'), m2=Sum('m2')).filter(
        #     block_num=self.object)
        # for part in slab_list:
        #     part['part_num'] = [part for part in
        #                         Slab.objects.values('part_num').filter(block_num=self.object,
        #                                                                thickness=part['thickness']).distinct()]
        #     for item in part['part_num']:
        #         item['item'] = [slab for slab in
        #                         self.object.slab.filter(block_num=self.object, thickness=part['thickness'],
        #                                                 part_num=item['part_num'])]
        kwargs['slab_list'] = self.object.get_slab_list()
        return super(ProductDetailView, self).get_context_data(**kwargs)

# {
#     1.5: {
#     1: [1, 2, 3],
#     2: [4, 5, 6]
# },
#     1.8: {
#         1: [1, 2, 3],
#     },
# }
