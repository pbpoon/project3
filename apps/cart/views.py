from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .cart import Cart
from .forms import PriceForm


def cart_detail(request):
    cart = Cart(request)
    items = cart.make_slab_list()
    object_list = []
    for item in items:
        for i in item:
            # priceform = PriceForm(initial={'price': cart.cart['price'].get(str(i['block_num']))})
            object_list.append({'item': i, 'price_form': PriceForm()})
    form = PriceForm()
    return render(request, 'cart/detail.html', {'object_list': object_list, 'form': form})


@require_POST
def cart_add(request):
    cart = Cart(request)
    chk = request.POST.getlist('check_box_list')
    cart.add(chk)
    return redirect('cart:index')
