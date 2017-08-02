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
    def add(self, ids=None, key=None):
        cart_lst = self.cart[key] if key else self.cart['slab_ids']
        cart_lst.extend(ids)
        cart_lst = list(set(cart_lst))
        self.save()

    # 把数据更新到session
    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        # 用modified属性设定为True的方法来修改session
        self.session.modified = True

    # 把product在cart删除
    def remove(self, ids, key=None):
        cart_list = self.cart[key] if key else self.cart['slab_ids']
        cart_list = list(set(cart_list) - set(ids))
        self.save()

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in
                   self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def make_slab_list(self, key=None):
        """
        :param key: 为string类型，为需要把cart中存的那个slab_id列表生成码单，默认不存参数是返回slab_ids
        :return: 返回列表类型
        """
        return self.make_slab_listt(key).extend(self.make_block_list(key))

    def make_slab_listt(self, key=None):
        key = key + '_slab_ids'
        slab_ids = self.cart[key] if key else self.cart['slab_ids']
        block_list = Product.objects.filter(slab__id__in=slab_ids).distinct()
        return [i for block in block_list for i in block.get_slab_list(slab_ids)]

    def make_block_list(self, key=None):
        key = key + '_block_ids'
        block_ids = self.cart[key] if key else self.cart['block_ids']
        block_list = Product.objects.filter(id__in=block_ids).all()
        return [i for block in block_list for i in block.get_block_list()]

    def make_price_list(self):
        slab_list = self.make_slab_list()
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
        slab_list = self.make_slab_list()
        count = len(slab_list)
        total_quantity = sum(Decimal(i['block_quantity']) for i in slab_list)
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
        'block_m2': Decimal('185.69'),
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
            _dict['block_m2'] = sum(Decimal(item['m2']) for item in lst if
                                    item['block_num'] == _dict['block_num'] and
                                    item['thickness'] == _dict[
                                        'thickness'])
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
