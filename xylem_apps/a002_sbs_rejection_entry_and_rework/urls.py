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

from xylem_apps.a000_xylem_master import serve

from . import views

app_name = serve.an_sbs_rejection_entry_and_rework
urlpatterns = [
    path('forms/qa_rejection_rework_form/', views.qa_rejection_rework_form, name='qa_rejection_rework_form'),
    path('forms/qa_rejection_rework_form/rre_validate_barcode/', views.rre_validate_barcode, name='rre_validate_barcode'),
    path('reports/qa_rejection_rework_report/<int:current_product_category_id>/', views.qa_rejection_rework_report, name='qa_rejection_rework_report'),
    path('reports/qa_rejection_rework_graphical_report/<int:current_product_category_id>/', views.qa_rejection_rework_graphical_report, name='qa_rejection_rework_graphical_report'),
    
    path('ajax_load_report_table/<int:current_product_category_id>/', views.ajax_load_report_table, name='ajax_load_report_table'),
    path('ajax_load_graph_data/', views.ajax_load_graph_data, name='ajax_load_graph_data'),
]
