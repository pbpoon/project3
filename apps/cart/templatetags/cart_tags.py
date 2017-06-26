# _*_ conding:utf-8 _*_
__author__ = 'pbpoon'
__date__ = '2017/6/26 14:41'

from django import template
from cart.cart import Cart

register = template.Library()


@register.inclusion_tag('cart/cart_info.html', takes_context=True)
def show_cart_info(context):
    request = context['request']
    cart = Cart(request)
    return cart.get_info()
