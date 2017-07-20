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
# '''生产订单'''
# urlpatterns += [
#     url(r'^order/$', views.ProcessOrderListView.as_view(), name='order_list'),
#     url(r'^order/create/$', views.ProcessOrderCreateView.as_view(), name='order_create'),
#     url(r'^order/update/(?P<pk>\d+)/$', views.ProcessOrderUpdateView.as_view(),
#         name='order_update'),
#     url(r'^order/(?P<pk>\d+)/$', views.ProcessOrderDetailView.as_view(), name='order_detail'),
# ]
