"""
URL configuration for xylem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path("", views.home, name="home")
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path("", Home.as_view(), name="home")
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path("blog/", include("blog.urls"))
"""
from django.contrib import admin
from django.urls import path
from . import views
from xylem_apps.a000_xylem_master import serve

app_name = serve.an_qa_report_and_reprocess
urlpatterns = [
    path("", views.home, name="home"),
    path("line_selection/<int:work_type>/", views.line_selection, name="line_selection"), 
    path("station_selection/<int:work_type>/<int:line_id>", views.station_selection, name="station_selection"), 
    path("report_page/<int:work_type>/<int:line_id>/<int:stn_id>", views.report_page, name="report_page"),
    path("reprocess_page/<int:work_type>/<int:line_id>/<int:stn_id>", views.reprocess_page, name="reprocess_page"),
    path("connect_server/", views.connect_server, name="connect_server"),
    path("server_get_report_data/", views.server_get_report_data, name="server_get_report_data"),
    path("server_get_reprocess_data/", views.server_get_reprocess_data, name="server_get_reprocess_data"),
    path("server_update_reprocess_data/", views.server_update_reprocess_data, name="server_update_reprocess_data"),
]
