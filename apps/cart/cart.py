# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/6 11:15'

from decimal import Decimal
from django.conf import settings
from products.models import Product


class Cart(object):
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
            cart['slab_ids'] = []
            cart['price'] = {}
        self.cart = cart

    # 添加product 到 cart
    def add(self, slab_ids):
        for id in slab_ids:
            if id not in self.cart['slab_ids']:
                self.cart['slab_ids'].append(id)
        self.make_price_list()
        self.save()

    # 把数据更新到session
    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        # 用modified属性设定为True的方法来修改session
        self.session.modified = True

    # 把product在cart删除
    def remove(self, slab_ids):
        for id in slab_ids:
            if id in self.cart['slab_ids']:
                self.cart['slab_ids'].remove(id)
        self.save()

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def make_slab_list(self):
        block_list = self.get_block_num()
        slab_ids = self.cart['slab_ids']
        return [i for block in block_list for i in block.get_slab_list(slab_ids)]

    def get_block_num(self):
        slab_ids = self.cart['slab_ids']
        block_list = Product.objects.filter(slab__id__in=slab_ids).distinct()
        return block_list

    def make_price_list(self):
        slab_list = self.make_slab_list()
        price_list = self.cart['price']
        for item in slab_list:
            price_list.setdefault(str(item['block_num'])+str(item['thickness']), 0)
        print(price_list)

    def update_price(self, block_num=None, thickness=None, price=None):
        if block_num and thickness and price:
            self.cart['price'][block_num][thickness] = price
            self.save()

    def order_item_list(self):
        slab_list = self.make_slab_list()
        price_list = self.cart['price']
        list = []
        for item in slab_list:
            lst = {}
            for key, val in item.items():
                for k, v in val.items():
                    lst = {'block_num': key, 'thickness': str(k), 'block_pics': str(v['block_pics']),
                           'block_m2': str(v['block_m2']),
                           'price': price_list[key][str(k)]}
                    list.append(lst)
        return list
