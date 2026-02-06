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
    2. Add a URL to urlpatterns:  path("    blog/", include("blog.urls"))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from xylem_apps.a000_xylem_master import serve

from . import views

# a000_xylem_master
# a001_qa_report_and_reprocess
# a002_sbs_rejection_entry_and_rework
# a003_smart_alerts
# a004_tools_management_system
# a005_qa_patrol_check
# a006_4m_digitalization
# a007_oee_monitoring
# a008_home_schemer
# a009_building_management_system
# a010_poka_yoke_monitoring
# a011_workflows

urlpatterns = [
    path("", views.custom_index, name="custom_index"),
    path("default/", views.index, name="index"),
    path("admin/", admin.site.urls),

    # Xylem apps
    path("", include("xylem_apps.a000_xylem_master.urls")),
    path(f"{serve.an_qa_report_and_reprocess}/", include("xylem_apps.a001_qa_report_and_reprocess.urls")),
    path(f"{serve.an_sbs_rejection_entry_and_rework}/", include("xylem_apps.a002_sbs_rejection_entry_and_rework.urls")),
    path(f"{serve.an_smart_alerts}/", include("xylem_apps.a003_smart_alerts.urls")),
    path(f"{serve.an_tools_management_system}/", include("xylem_apps.a004_tools_management_system.urls")),
    path(f"{serve.an_qa_patrol_check}/", include("xylem_apps.a005_qa_patrol_check.urls")),
    path(f"{serve.an_4m_digitalization}/", include("xylem_apps.a006_4m_digitalization.urls")),
    path(f"{serve.an_oee_monitoring}/", include("xylem_apps.a007_oee_monitoring.urls")),
    path(f"{serve.an_home_schemer}/", include("xylem_apps.a008_home_schemer.urls")),
    path(f"{serve.an_building_management_system}/", include("xylem_apps.a009_building_management_system.urls")),
    path(f"{serve.an_poka_yoke_monitoring}/", include("xylem_apps.a010_poka_yoke_monitoring.urls")),
    path(f"{serve.an_workflows}/", include("xylem_apps.a011_workflows.urls")),
] +\
static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) +\
static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# handler404 = "xylem.views.my_custom_page_not_found_view"
handler500 = "xylem.views.custom500"