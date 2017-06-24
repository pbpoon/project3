from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .cart import Cart
from .forms import PriceForm


def cart_detail(request):
    cart = Cart(request)
    items = cart.make_slab_list()
    for item in items:
        for thickness_key, thickness in item.items():
            thickness['price_form'] = PriceForm(initial={'price': cart.cart['price'].get(str(thickness_key))})
    return render(request, 'cart/detail.html', {'object_list': items})


@require_POST
def cart_add(request):
    cart = Cart(request)
    chk = request.POST.getlist('check_box_list')
    cart.add(chk)
    return redirect('cart:index')
