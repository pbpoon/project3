from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .cart import Cart
from django.contrib import messages
from utils import str_to_list, AddExcelForm


def cart_detail(request):
    cart = Cart(request)
    object_list = cart.make_items_list()
    import_slabs = cart.make_import_slab_list()
    import_slab_form = AddExcelForm()
    for item in object_list:
        item['slab_ids'] = item['block_num'] if item['thickness'] == '荒料' \
            else [id for part in item['part_num'].values() for id in part['slabs']]
    context = {
        'object_list': object_list,
        'import_slabs': import_slabs,
        'form': import_slab_form,
    }

    return render(request, 'cart/detail.html', context)


@require_POST
def cart_add(request):
    cart = Cart(request)
    ids = request.POST.getlist('check_box_list')
    key = request.POST.get('key', None)
    block = int(request.POST.get('block', 0))
    cart.add(ids, key=key, block=block)
    path = request.META.get('HTTP_REFERER')
    messages.success(request, '已成功更新选择列表！')
    return redirect(path)


@require_POST
def cart_remove(request):
    cart = Cart(request)
    item = request.POST.get('item')
    block = int(request.POST.get('block', 0))
    key = request.POST.get('key', None)
    cart.remove(str_to_list(item), key=key, block=block)
    path = request.META.get('HTTP_REFERER')
    return redirect(path)


@require_POST
def cart_update_price(request):
    cart = Cart(request)
    price = request.POST.get('price')
    item = request.POST.get('item')
    item = ''.join(item.split(','))
    cart.update_price(item, price)
    return redirect('cart:index')


def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect('cart:index')


@require_POST
def import_slabs(request):
    item_form = AddExcelForm(request.POST, request.FILES)
    if item_form.is_valid():
        f = item_form.files.get('file')
        if f:
            from cart.cart import Cart
            cart = Cart(request)
            cart.save_import_slab_list(f)
    return redirect('cart:index')


@require_POST
def remove_import_slabs(request):
    cart = Cart(request)
    block_num = request.POST.get('block_num')
    thickness = request.POST.get('thickness')
    cart.remove_import_slabs(block_num, thickness)
    return redirect('cart:index')


def show_import_slabs(request):
    pass
