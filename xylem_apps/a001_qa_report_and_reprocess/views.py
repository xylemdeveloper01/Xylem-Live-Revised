import json, requests
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.cache import caches

from xylem_apps.a000_xylem_master.tests import view_eligibity_test
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom
from xylem_apps.a000_xylem_master import serve 

from .models import ReprocessRecordLog


work_type = None

line_key_list = serve.Apps.A001QAReportAndReprocess.line_key_list
stn_key_list = serve.Apps.A001QAReportAndReprocess.stn_key_list

report_wt = serve.Apps.A001QAReportAndReprocess.report_wt
reprocess_wt = serve.Apps.A001QAReportAndReprocess.reprocess_wt

wt_dict = { report_wt : "Report", reprocess_wt : "Reprocess" }

remark_dict = { "121" : "Current Station Failed", "122" : "Current Station Already Run" }

a001_cache = caches[serve.an_qa_report_and_reprocess]

@login_required(login_url="login")
def home(request):
    context = {
        "parent" : "projects",
        "segment" : "QA Report and Reprocess",
        "root" : [
            { "name" : "QA Report and Reprocess", "url" : reverse( "a001:home" ) },
        ],
        "child" : "Home",
        "selection_list": [
            { "name": wt_dict[report_wt], "url" : reverse( "a001:line_selection", args = (report_wt, )) },
            { "name": wt_dict[reprocess_wt], "url" : reverse( "a001:line_selection", args = (reprocess_wt, )) },
        ]
    }
    return render(request, "a001/T01_selections.html", context)


@login_required(login_url="login")
def line_selection(request, work_type):
    line_list = []
    master_dict = a001_cache.get(serve.Apps.A001QAReportAndReprocess.cache_key_of_master_dict)
    for i in master_dict:
        line_list.append(
            { "name": master_dict[i][line_key_list[0]], "url" : reverse( "a001:station_selection", args = ( work_type, i, ) ) }
        )
    context = {
        "parent" : "projects",
        "segment" : "QA Report and Reprocess",
        "root" : [
            { "name" : "QA Report and Reprocess", "url" : reverse( "a001:home" ) },
            { "name" : wt_dict[work_type], "url": reverse( "a001:line_selection", args = ( work_type, ) )},
        ],
        "child" : f"{wt_dict[work_type]} Area Line Selection",
        "selection_list": line_list ,
    }
    return render(request, "a001/T01_selections.html", context)


@login_required(login_url="login")
def station_selection(request, work_type, line_id):
    stn_list = []
    master_dict = a001_cache.get(serve.Apps.A001QAReportAndReprocess.cache_key_of_master_dict)
    line_name = master_dict[line_id][line_key_list[0]]
    page = "report_page" if work_type==1 else "reprocess_page" if work_type==2 else None
    next_page_url = f"a001:{page}"
    for i in master_dict[line_id][line_key_list[1]]:
        stn_list.append(
            { "name" : master_dict[line_id][line_key_list[1]][i][stn_key_list[0]], "url" : reverse( next_page_url , args = ( work_type, line_id, i, ) ) }
        )

    context = {
        "parent" : "projects",
        "segment" : "QA Report and Reprocess",
        "root" : [
            { "name" : "QA Report and Reprocess", "url" : reverse( "a001:home" ) },
            { "name" : wt_dict[work_type], "url": reverse( "a001:line_selection", args = ( work_type, ) )},
            { "name" : line_name, "url": reverse( "a001:station_selection", args = ( work_type, line_id, ) )},
        ],
        "child" : f"{wt_dict[work_type]} Area Station Selection",
        "selection_list": stn_list ,
    }    
    return render(request, "a001/T01_selections.html", context)


@login_required(login_url="login")
def report_page(request, work_type, line_id, stn_id):

    master_dict = a001_cache.get(serve.Apps.A001QAReportAndReprocess.cache_key_of_master_dict)
    line_name = master_dict[line_id][line_key_list[0]]
    station_name = master_dict[line_id][line_key_list[1]][stn_id][stn_key_list[0]]
    context = {
        "parent" : "projects",
        "segment" : "QA Report and Reprocess",
        "root" : [
            { "name" : "QA Report and Reprocess", "url" : reverse( "a001:home" ) },
            { "name" : wt_dict[work_type], "url": reverse( "a001:line_selection", args = ( work_type, ) )},
            { "name" : line_name, "url": reverse( "a001:station_selection", args = ( work_type, line_id, ) )},
            { "name" : station_name, "url": reverse( "a001:report_page", args = ( work_type, line_id, stn_id ) )},
        ],
        "child" : f"{wt_dict[work_type]} page",
        "connect_server_url" : reverse( "a001:connect_server" ),
        "server_get_data_url" : reverse( "a001:server_get_report_data" ),
        "work_type" : work_type,
        "line" : { "id": line_id, "name": line_name },
        "stn" : { "id": stn_id, "name": station_name },
    } 
    return render(request, "a001/T02_report_page.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.All_designations],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def reprocess_page(request, work_type, line_id, stn_id):
    master_dict = a001_cache.get(serve.Apps.A001QAReportAndReprocess.cache_key_of_master_dict)
    line_name = master_dict[line_id][line_key_list[0]]
    station_name = master_dict[line_id][line_key_list[1]][stn_id][stn_key_list[0]]
    context = {
        "parent" : "projects",
        "segment" : "QA Report and Reprocess",
        "root" : [
            { "name" : "QA Report and Reprocess", "url" : reverse( "a001:home" ) },
            { "name" : wt_dict[work_type], "url": reverse( "a001:line_selection", args = ( work_type, ) )},
            { "name" : line_name, "url": reverse( "a001:station_selection", args = ( work_type, line_id, ) )},
            { "name" : station_name, "url": reverse( "a001:reprocess_page", args = ( work_type, line_id, stn_id ) )},
        ],
        "child" : f"{wt_dict[work_type]} page",
        "connect_server_url" : reverse( "a001:connect_server" ),
        "server_get_data_url" : reverse( "a001:server_get_reprocess_data" ),
        "server_update_data_url" : reverse( "a001:server_update_reprocess_data" ),
        "work_type" : work_type,
        "line" : { "id": line_id, "name": line_name },
        "stn" : { "id": stn_id, "name": station_name },
    }
    return render(request, "a001/T03_reprocess_page.html", context)


@login_required(login_url="login")
def connect_server(request):
    data = json.loads(request.body.decode("utf-8"))
    cid = serve.get_from_background_worker_api(serve.a001_mainserver_connect_url+f"{data['work_type']}/{data['line_id']}/{data['stn_id']}").json()
    return JsonResponse({"connection_id": cid})


@login_required(login_url="login")
def server_get_report_data(request):
    data = json.loads(request.body.decode("utf-8"))
    connection_id = data["connection_id"]
    serialNo = data["serialNo"]
    fromDate = data["fromDate"]
    toDate = data["toDate"]
    payload = {
		"connection_id": connection_id,
		"serialNo": serialNo,
		"fromDate": fromDate,
		"toDate": toDate,
	}
    send_dict = serve.get_from_background_worker_api(serve.a001_mainserver_get_data_url, method="POST", json=payload).json()
    head_msg = ""
    if send_dict:
        if data["serialNo"]:
            head_msg = f"Report for the Serial No : {serialNo}"
        elif fromDate or toDate:
            head_msg = f"Report from {fromDate} to {toDate}"
    return JsonResponse({"head_msg": head_msg, "report_data": send_dict})


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.All_designations],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def server_get_reprocess_data(request):
    data = json.loads(request.body.decode("utf-8"))
    connection_id = data["connection_id"]
    serialNo = data["serialNo"]
    payload = {
		"connection_id": connection_id,
		"serialNo": serialNo,
	}
    send_dict = serve.get_from_background_worker_api(serve.a001_mainserver_get_data_url, method="POST", json=payload).json()
    head_msg = ""
    if send_dict:
        head_msg = f"Final data for the Serial No : {serialNo}"
    return JsonResponse({"head_msg": head_msg, "report_data": send_dict})


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.All_designations],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def server_update_reprocess_data(request):
    data = json.loads(request.body.decode("utf-8"))
    connection_id = data["connection_id"]
    serialNo = data["serialNo"]
    remarks = remark_dict[data["remarks"]]
    user_id = request.user
    payload = {
		"connection_id": connection_id,
		"serialNo": serialNo,
		"remarks": remarks,
	}
    update_reponse = serve.get_from_background_worker_api(serve.a001_mainserver_update_data_url, method="POST", json=payload).json()
    if update_reponse:
        ReprocessRecordLog.objects.create(
            user_id=user_id,
            serialno=serialNo,
            db_name=update_reponse["db_name"],
            table_name=update_reponse["table_name"],
            i_remarks=data["remarks"],
        )
        update_reponse = 1
        send_dict = {"update_reponse": update_reponse, "serialNo": serialNo}
    else:
        send_dict = {"update_reponse": update_reponse}
    return JsonResponse(send_dict)
    