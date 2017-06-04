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
'''合作伙伴'''
urlpatterns = [
    url(r'^supplier/$', views.SupplierListView.as_view(), name='supplier_list'),
    url(r'^supplier/(?P<pk>\d+)/$', views.SupplierDetailView.as_view(), name='supplier'),
    url(r'^supplier/create/$', views.SupplierCreateView.as_view(), name='supplier_create'),
    url(r'^supplier/delete/(?P<pk>\d+)/$', views.SupplierDeleteView.as_view(), name='supplier_delete'),
    url(r'^supplier/update/(?P<pk>\d+)$', views.SupplierUpdateView.as_view(), name='supplier_update'),
]
'''采购订单'''
urlpatterns += [
    url(r'^purchase_order/$', views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
    url(r'^purchase_order/(?P<pk>\d+)/$', views.PurchaseOrderDetailView.as_view(), name='purchase_order'),
    url(r'^purchase_order/create/$', views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    # url(r'^supplier/delete/(?P<pk>\d+)/$', views.SupplierDeleteView.as_view(), name='supplier_delete'),
    # url(r'^supplier/update/(?P<pk>\d+)$', views.SupplierUpdateView.as_view(), name='supplier_update'),
]