# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/6 11:15'

from decimal import Decimal
from django.conf import settings
from products.models import Product, Slab
from utils import ImportData


class Cart(object):
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
            cart['slab_ids'] = []
            cart['price'] = {}
            cart['import_slabs'] = []
            cart['import_block'] = []
            cart['block_ids'] = []
        self.cart = cart

    # 添加product 到 cart
    def add(self, ids=None, key=None, block=False):
        suffix = 'slab_ids'
        if block:
            suffix = 'block_ids'
        if key:
            suffix = key + '_' + suffix
        self.cart.setdefault(suffix, []).extend(ids)
        self.cart[suffix] = list(set(self.cart[suffix]))
        self.save()

    # 把数据更新到session
    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        # 用modified属性设定为True的方法来修改session
        self.session.modified = True

    # 把product在cart删除
    def remove(self, ids, key=None, block=False):
        suffix = 'slab_ids'
        if block:
            suffix = 'block_ids'
        if key:
            suffix = key + '_' + suffix
        self.cart[suffix] = list(set(self.cart[suffix]) - set(ids))
        self.save()

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in
                   self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def make_items_list(self, key=None):
        """
        :param key: 为string类型，为需要把cart中存的那个cart的list的前序
        :return: 返回列表类型
        """
        return self._make_slab_list(key) + self._make_block_list(key)

    def _make_slab_list(self, key=None):
        suffix = 'slab_ids'
        slab_ids = self.cart.get(key + '_' + suffix) if key else self.cart.get(suffix)
        slab_list = Product.objects.filter(slab__id__in=slab_ids).distinct() if slab_ids else []
        return [i for block in slab_list for i in block.get_slab_list(slab_ids)]

    def _make_block_list(self, key=None):
        suffix = 'block_ids'
        block_ids = self.cart.get(key + '_' + suffix) if key else self.cart.get(suffix)
        block_list = Product.objects.filter(block_num__in=block_ids).all() if block_ids else []
        return [i for block in block_list for i in block.get_block_list()]

    def make_price_list(self):
        slab_list = self.make_items_list()
        price_list = self.cart['price']
        for item in slab_list:
            price_list.setdefault(
                str(item['block_num']) + str(item['thickness']), 0)

    def update_price(self, item, price=None):
        price_list = self.cart['price']
        if item and price:
            try:
                price_list[item] = int(price)
            except ValueError as e:
                return
            self.save()

    def get_info(self):
        slab_list = self.make_items_list()
        count = len(slab_list)
        total_quantity = sum(Decimal(i['quantity']) for i in slab_list)
        return {'count': count, 'total_m2': total_quantity}

    def save_import_slab_list(self, f):
        importer = ImportData(f)
        self.cart['import_slabs'].extend(importer.data)
        self.save()

    def make_import_slab_list(self):
        """
        返回的是列表，格式如下：
        [{'block_num': '4901',
        'thickness': '1.50',
        'block_pics': 41,
        'quantity': Decimal('185.69'),
         'part_count': 4,

         'slabs': [
         {'block_num': '4901',
         'thickness': '1.50',
         'part_num': '1',
          'line_num': 1,
          'long': '290.00',
           'high': '156.00',
           'kl1': '10.00',
            'kl2': '10.00',
            'kh1': '10.00',
            'kh2': '10.00',
            'm2': '4.53'}
            ]
        """
        lst = self.cart['import_slabs']
        _set = set((item['block_num'], item['thickness']) for item in lst)
        _list = [{'block_num': num, 'thickness': thick} for num, thick in
                 list(_set)]
        for _dict in _list:
            _dict['block_pics'] = len(
                [item for item in lst if item['block_num'] == _dict['block_num'] and
                 item['thickness'] == _dict['thickness']])
            _dict['quantity'] = sum(Decimal(item['m2']) for item in lst if
                                    item['block_num'] == _dict['block_num'] and
                                    item['thickness'] == _dict[
                                        'thickness'])
            _dict['unit'] = 'm2'
            _dict['part_count'] = len(set([item['part_num'] for item in lst if
                                           item['block_num'] == _dict[
                                               'block_num'] and item[
                                               'thickness'] == _dict[
                                               'thickness']]))
            _dict['slabs'] = [item for item in lst if
                              item['block_num'] == _dict['block_num'] and item[
                                  'thickness'] == _dict[
                                  'thickness']]
        return _list

    def get_import_slab_list_by_parameter(self, block_num=None, thickness=None):
        if not block_num and not thickness:
            raise ValueError('没有足够参数')
        import_slab_list = self.make_import_slab_list()
        for item in import_slab_list:
            if item['block_num'] == str(block_num) and item['thickness'] == str(thickness):
                return item['slabs']
        return None

    def remove_import_slabs(self, block_num=None, thickness=None):
        lst = self.cart['import_slabs']
        for item in lst[:]:
            '''
            lst[:]实际是lst的拷贝，所以遍历删除的时候不会因为删除符合条件的遍历item，令原遍历个数减少而删除不完全
            可以参考http://www.cnblogs.com/bananaplan/p/remove-listitem-while-iterating.html
            '''
            if item['block_num'] == block_num and item['thickness'] == thickness:
                lst.remove(item)
        self.save()
