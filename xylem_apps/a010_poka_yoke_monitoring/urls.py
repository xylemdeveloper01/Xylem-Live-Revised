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

app_name = serve.an_poka_yoke_monitoring
urlpatterns = [
    path('awaiting_poka_yoke_inspections/<int:current_product_category_id>/', views.awaiting_poka_yoke_inspections, name='awaiting_poka_yoke_inspections'),
    path('awaiting_poka_yoke_inspections/<int:current_product_category_id>/<int:current_production_line_id>/', views.awaiting_poka_yoke_inspections, name='awaiting_poka_yoke_inspections_with_pl_id'),
    path('poka_yoke_inspection_additon/', views.poka_yoke_inspection_additon, name='poka_yoke_inspection_additon'),
    path('poka_yoke_tree/<int:current_product_category_id>/', views.poka_yoke_tree, name='poka_yoke_tree'),
    path('poka_yoke_fruit_clusters/<int:current_production_line_id>/', views.poka_yoke_fruit_clusters, name='poka_yoke_fruit_clusters'),
    path('poka_yoke_fruits/<int:current_production_station_id>/', views.poka_yoke_fruits, name='poka_yoke_fruits'),
]
