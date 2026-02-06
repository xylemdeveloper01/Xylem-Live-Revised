"""
URL configuration for xylem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views
from xylem_apps.a000_xylem_master import serve

app_name = serve.an_building_management_system
urlpatterns = [
    path('pc_dashboard/', views.pc_dashboard, name='pc_dashboard'),
    path('get_pc_dashboard_data/', views.get_pc_dashboard_data, name='get_pc_dashboard_data'),

    path('wc_dashboard/', views.wc_dashboard, name='wc_dashboard'),
    path('get_wc_dashboard_data/', views.get_wc_dashboard_data, name='get_wc_dashboard_data'),
]
