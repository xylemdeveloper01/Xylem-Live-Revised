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


app_name = serve.an_oee_monitoring
urlpatterns = [
    path('oee_dashboard/', views.oee_dashboard, name='oee_dashboard'),
    path('get_dashboard_data/', views.get_dashboard_data, name='get_dashboard_data'),
    path('oee_event_response/<int:current_pagination_option_id>/<int:current_page_num>/', views.oee_event_response, name='oee_event_response'),
    path('production_plan/<int:current_product_category_id>/', views.production_plan_init, name='production_plan_init'),
    path('production_plan/<int:current_product_category_id>/<int:current_month_id>/<int:current_year_id>/', views.production_plan, name='production_plan'),
    path('production_plan/release/<int:production_line_id>/<int:month_id>/<int:year_id>/', views.production_plan_release, name='production_plan_release'),
    path('production_plan/release/save/<int:production_line_id>/<int:month_id>/<int:year_id>/', views.production_plan_release_save, name='production_plan_release_save'),
    path('production_plan/modify/<int:production_line_id>/<int:month_id>/<int:year_id>/', views.production_plan_modify, name='production_plan_modify'),
    path('production_plan/modify/save/<int:production_line_id>/<int:month_id>/<int:year_id>/', views.production_plan_modify_save, name='production_plan_modify_save'),
    path('production_plan/view/<int:production_line_id>/<int:month_id>/<int:year_id>/', views.production_plan_view, name='production_plan_view'),
    path('oee_report/home/',views.oee_report,name='oee_report'),
    path('oee_report/dashboard_type/<int:current_product_category_id>/',views.oee_report_dashboard_type,name='oee_report_dashboard_type'),
    path('ajax_load_oee_report_dashboard_type/',views.ajax_load_oee_report_dashboard_type,name='ajax_load_oee_report_dashboard_type'),
]

