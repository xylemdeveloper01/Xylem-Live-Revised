import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse

import xylem.custom_messages.constants as custom_messages
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom, view_eligibity_test
from xylem_apps.a000_xylem_master import serve


@login_required(login_url="/accounts/login/")
def pc_dashboard(request):
    context = {
        "parent": "Dashboards",
        "segment": "Power Consumption Dashboard",
        "get_pc_dashboard_data_url": reverse("a009:get_pc_dashboard_data"),
    }
    return render(request, 'a009/pc_dashboard.html', context)
    # return render(request, 'a009/carousal_c.html', context)


@login_required(login_url="/accounts/login/")
def get_pc_dashboard_data(request):
    if request.method == "GET":
	    return JsonResponse(serve.get_from_background_worker_api(serve.a009_get_pc_dashboard_dict_url).json())


@login_required(login_url="/accounts/login/")
def wc_dashboard(request):
    context = {
        "parent" : "Dashboards",
        "segment"  : "Water Consumption Dashboard",
        "get_wc_dashboard_data_url": reverse("a009:get_wc_dashboard_data"),
    }
    return render(request, 'a009/wc_dashboard.html', context)


@login_required(login_url="/accounts/login/")
def get_wc_dashboard_data(request):
    if request.method == "GET":
	    return JsonResponse(serve.get_from_background_worker_api(serve.a009_get_wc_dashboard_dict_url).json())