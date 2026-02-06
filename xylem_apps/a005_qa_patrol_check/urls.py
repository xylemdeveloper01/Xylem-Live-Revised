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

app_name = serve.an_qa_patrol_check
urlpatterns = [
    path('forms/qa_patrol_inspection_selection/', views.qa_patrol_inspection_selection, name='qa_patrol_inspection_selection'),
    path('forms/qa_patrol_inspection/<int:qa_pcs_id>/', views.qa_patrol_inspection, name='qa_patrol_inspection'),
    path('forms/qa_patrol_inspection/single_view/<int:qa_insp_id>/', views.qa_patrol_inspection_single_view, name='qa_patrol_inspection_single_view'),
    path('approvals/qa_patrol_inspection_approval/<int:current_pagination_option_id>/<int:current_page_num>/', views.qa_patrol_inspection_approval, name='qa_patrol_inspection_approval'),
    path('approvals/qa_patrol_inspection_approval/<int:current_pagination_option_id>/<int:current_page_num>/<int:qa_insp_id>', views.qa_patrol_inspection_approval_view, name='qa_patrol_inspection_approval_view'),
    path('reports/qa_patrol_report/selection/', views.qa_patrol_report_selection, name='qa_patrol_report_selection'),
    path('reports/qa_patrol_report/view/<int:ref_qa_insp_id>/', views.qa_patrol_report_view, name='qa_patrol_report_view'),
    path('ajax_get_inspection_table/', views.ajax_get_inspection_table, name='ajax_get_inspection_table'),
]
