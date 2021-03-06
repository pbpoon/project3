"""project3 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.cart_detail, name='index'),
    url(r'^add/$', views.cart_add, name='add'),
    url(r'^remove/$', views.cart_remove, name='remove'),
    url(r'^remove-import/$', views.remove_import_slabs, name='remove_import'),
    url(r'^update-price/$', views.cart_update_price, name='update_price'),
    url(r'^clear/$', views.cart_clear, name='clear'),
    url(r'^import_slab/$', views.import_slabs, name='import_slab')
]
