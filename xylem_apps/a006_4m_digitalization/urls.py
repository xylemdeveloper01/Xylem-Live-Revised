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

app_name = serve.an_4m_digitalization
urlpatterns = [
    path('forms/four_m_form/', views.four_m_form, name='four_m_form'),
    path('approvals/four_m_approval/<int:current_pagination_option_id>/<int:current_page_num>/', views.four_m_approval, name='four_m_approval'),
    path('approvals/four_m_approval/<int:current_pagination_option_id>/<int:current_page_num>/<int:four_m_form_id>', views.four_m_approval_view, name='four_m_approval_view'),
    path('reports/four_m_report/filter/', views.four_m_report, name='four_m_report_filter'),
    path('reports/four_m_report/view/<int:form_id>/', views.four_m_report_view, name='four_m_report_view'),
    
    path('ajax_report_table/', views.ajax_report_table, name='ajax_report_table'),
]
