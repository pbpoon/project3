from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .cart import Cart
from .forms import PriceForm

import re


def cart_detail(request):
    cart = Cart(request)
    items = cart.make_slab_list()
    for item in items:
        item['price_form'] = PriceForm(
            initial={'price': cart.cart['price'].get(str(item['block_num']) + str(item['thickness']), 0)})
        item['slab_ids'] = [id for part in item['part_num'].values() for id in part['slabs']]

    return render(request, 'cart/detail.html', {'object_list': items})


@require_POST
def cart_add(request):
    cart = Cart(request)
    chk = request.POST.getlist('check_box_list')
    cart.add(chk)
    return redirect('cart:index')


@require_POST
def cart_remove(request):
    cart = Cart(request)
    item = request.POST.get('item')
    s, *t, r = re.split(r'[\[|,\s|\]]\s', item)
    t.append(s.split('[')[1])
    t.append(r.split(']')[0])
    cart.remove(t)
    return redirect('cart:index')


@require_POST
def cart_update_price(request):
    cart = Cart(request)
    price = request.POST.get('price')
    item = request.POST.get('item')
    item = ''.join(item.split(','))
    cart.update_price(item, price)
    return redirect('cart:index')


def cart_slablist_detail(request):
    cart = Cart(request)
    item = request.GET.get('item')
