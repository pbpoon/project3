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
            print(self.cart)
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


                # def __iter__(self):
                #     product_ids = self.cart.keys()
                #     products = Product.objects.filter(id__in=product_ids)
                #     for product in products:
                #         self.cart[str(product.id)]['product'] = product
                #     # 需要改寫這個forvalues的方法
                #     for item in self.cart.values():
                #         item['price'] = Decimal(item['price'])
                #         item['total_price'] = item['price'] * item['quantity']
                #         yield item
                #     print(self.cart)
                #
                #
                # def __len__(self):
                #     return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def make_slab_list(self):
        block_list = self.get_block_num()
        slab_ids = self.cart['slab_ids']
        return (block.get_slab_list(slab_ids) for block in block_list)

    def get_block_num(self):
        slab_ids = self.cart['slab_ids']
        block_list = Product.objects.filter(slab__id__in=slab_ids).distinct()
        return block_list

    def make_price_list(self):
        block_list = self.get_block_num()
        for block in block_list:
            if block.id not in self.cart['price'].keys():
                self.cart['price'][block.id] = 0

    def update_price(self, block_id, price):
        self.cart['price'][block_id] = price
        self.save()
