from django.conf.urls import url
from . import views

'''客户信息'''
urlpatterns = [
    url(r'^customer/$', views.CustomerInfoListView.as_view(),
        name='customer_list'),
    url(r'^customer/create/$', views.CustomerInfoCreateView.as_view(),
        name='customer_create'),
    url(r'^customer/(?P<pk>\d+)/$', views.CustomerInfoDetailView.as_view(),
        name='customer_detail'),
    url(r'^customer/update/(?P<pk>\d+)/$', views.CustomerInfoUpdateView.as_view(),
        name='customer_update'),
    url(r'^customer/delete/(?P<pk>\d+)/$', views.CustomerInfoDeleteView.as_view(),
        name='customer_delete'),
    url(r'^import/$', views.ImportView.as_view(),
        name='import'),
    url(r'^get-city-lst/$', views.get_city_info,
        name='get_city_lst'),
]
'''销售订单'''
urlpatterns += [
    url(r'^order/$', views.SalesOrderListView.as_view(), name='order_list'),
    url(r'^order/add/$', views.SalesOrderAddView.as_view(), name='order_add'),
    url(r'^order/create/$', views.SalesOrderCreateView.as_view(), name='order_create'),
    url(r'^order/update/item/(?P<pk>\d+)/$', views.SalesOrderUpdateItemView.as_view(),
        name='order_update_item'),
    url(r'^order/update/info/(?P<pk>\d+)/$', views.SalesOrderUpdateInfoView.as_view(),
        name='order_update_info'),
    url(r'^order/(?P<pk>\d+)/$', views.SalesOrderDetailView.as_view(), name='order_detail'),
    url(r'^order/pickup/create/(?P<salesorder>\d+)/$', views.PickUpCreateView.as_view(),
        name='pickup_create'),
    url(r'^order/pickup/(?P<pk>\d+)/$', views.PickupDetailView.as_view(),
        name='pickup_detail'),
    url(r'^order/pickup/delete/(?P<pk>\d+)/$', views.PickUpDeleteView.as_view(),
        name='pickup_delete'),
]
# """订单状态操作"""
# urlpatterns += [
#                    url(r'^order/(?P<pk>\d+)/$', views.SalesOrderDetailView.as_view(),
#                        name='order_detail'),]
