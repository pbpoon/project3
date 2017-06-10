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

'''服务商'''
urlpatterns = [
    url(r'^service/$', views.ServiceProviderListView.as_view(), name='serviceprovider_list'),
    url(r'^service/(?P<pk>\d+)/$', views.ServiceProviderDetailView.as_view(), name='serviceprovider_detail'),
    url(r'^service/create/$', views.ServiceProviderCreateView.as_view(), name='serviceprovider_create'),
    url(r'^service/update/(?P<pk>\d+)/$', views.ServiceProviderUpdateView.as_view(), name='serviceprovider_update'),
    url(r'^service/delete/(?P<pk>\d+)/$', views.ServiceProviderUpdateView.as_view(), name='serviceprovider_delete'),
]
