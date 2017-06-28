# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/6 11:15'

from decimal import Decimal
from django.conf import settings
from products.models import Product, Slab
import xlrd


class Cart(object):
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
            cart['slab_ids'] = []
            cart['price'] = {}
            cart['import_slabs'] = []
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
            price_list.setdefault(str(item['block_num']) + str(item['thickness']), 0)
        print(price_list)

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
        total_m2 = sum(Decimal(i['block_m2']) for i in slab_list)
        return {'count': count, 'total_m2': total_m2}

    def import_slab_list(self, f):
        data = xlrd.open_workbook(file_contents=f.read())
        table = data.sheets()[0]
        nrows = table.nrows  # 总行数
        colnames = table.row_values(0)  # 表头列名称数据
        lst = []
        for rownum in range(1, nrows):
            rows = table.row_values(rownum)
            item = {}
            for key, row in zip(colnames, rows):
                if not row:
                    if key == 'long' and key == 'high':
                        raise ValueError('有长或宽没有数值!')
                if key == 'part_num':
                    if not row:
                        raise ValueError('有夹号没有数值！')
                    item[key] = str(row).split('.')[0]
                elif key == 'block_num':
                    if not row:
                        raise ValueError('有荒料编号没有数值！')
                    item[key] = Product.objects.filter(block_num=str(row).split('.')[0])[0].block_num_id
                elif key == 'line_num':
                    if not row:
                        raise ValueError('有序号号没有数值！')
                    item[key] = int(row)
                else:
                    if row:
                        item[key] = '{0:.2f}'.format(row)
                    else:
                        item[key] = 0
            k1 = 0
            k2 = 0
            if item.get('kl1') and item.get('kh1'):
                k1 = Decimal(item['kl1']) * Decimal(item['kh1']) / 100000
            if item.get('kl2') and item.get('kh2'):
                k2 = Decimal(item['kl2']) * Decimal(item['kh2']) / 100000
            item['m2'] = '{0:.2f}'.format(Decimal(item['long']) * Decimal(item['high']) / 10000 + k1 + k2)
            lst.append(item)
        self.cart['import_slabs'].extend(lst)
        self.save()

    def show_import_slab_list(self):
        lst = self.cart['import_slabs']
        _set = set((item['block_num'], item['thickness']) for item in lst)
        _list = [dict(block_num=num, thickness=thick) for num, thick in list(_set)]
        for _dict in _list:
            _dict['block_pics'] = len([item for item in lst if
                                       item['block_num'] == _dict['block_num'] and item['thickness'] == _dict[
                                           'thickness']])
            _dict['block_m2'] = sum(Decimal(item['m2']) for item in lst if
                                    item['block_num'] == _dict['block_num'] and item['thickness'] == _dict[
                                        'thickness'])
            _dict['part_count'] = len(set([item['part_num'] for item in lst if
                                           item['block_num'] == _dict['block_num'] and item['thickness'] == _dict[
                                               'thickness']]))
            _dict['slabs'] = [item for item in lst if
                              item['block_num'] == _dict['block_num'] and item['thickness'] == _dict[
                                  'thickness']]
        return _list

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
