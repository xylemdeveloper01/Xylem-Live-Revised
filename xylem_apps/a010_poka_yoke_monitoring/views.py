import datetime, time
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from collections import defaultdict

import xylem.custom_messages.constants as custom_messages
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom, view_eligibity_test
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import PyPsMapping

from .pms_serve import get_pyps_maps_of_awaiting_inspections, get_poka_yoke_tree_dict_of_pc, get_poka_yoke_fruit_clusters_dict, get_poka_yoke_fruits_dict
from .models import PokaYokeInspections


inspec_ok = serve.Apps.A010PokaYokeMonitoring.inspec_ok
inspec_nok = serve.Apps.A010PokaYokeMonitoring.inspec_nok
inspec_waiting = serve.Apps.A010PokaYokeMonitoring.inspec_waiting

@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Interns_or_Trainees],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def awaiting_poka_yoke_inspections(request, current_product_category_id, current_production_line_id=None):
	product_categories = serve.get_product_categories()
	current_product_category = None
	pyps_maps_of_awaiting_inspections_dic = {}
	production_lines = None
	current_production_line = None
	pl_pyps_maps_of_awaiting_inspections_dic = {}
	for pc in product_categories:
		pyps_maps_of_awaiting_inspections = get_pyps_maps_of_awaiting_inspections(product_category_id=pc.icode)
		if pyps_maps_of_awaiting_inspections.exists():
			pyps_maps_of_awaiting_inspections_dic[pc.icode] = pyps_maps_of_awaiting_inspections if pc.icode == current_product_category_id else ""
	if not pyps_maps_of_awaiting_inspections_dic:
		messages.success(request, "All inpsections carried out successfully!")
	elif not (current_product_category_id in pyps_maps_of_awaiting_inspections_dic and pyps_maps_of_awaiting_inspections_dic):
		return redirect('a010:awaiting_poka_yoke_inspections', next(iter(pyps_maps_of_awaiting_inspections_dic)), )
	else:
		production_station_id_list =list(pyps_maps_of_awaiting_inspections_dic[current_product_category_id].values_list("production_station_i", flat=True))
		production_lines = serve.get_production_lines_of_pss(production_station_id_list=production_station_id_list)
		if current_production_line_id:
			current_production_line = serve.get_icode_object(current_production_line_id)
			if not current_production_line in production_lines:
				current_production_line = production_lines.first()
		else:
			current_production_line = production_lines.first()
		production_stations = serve.get_production_stations(production_line=current_production_line).filter(icode__in=production_station_id_list)
		for production_station in production_stations:
			pl_pyps_maps_of_awaiting_inspections_dic[production_station] = pyps_maps_of_awaiting_inspections_dic[current_product_category_id].filter(production_station_i=production_station)
		current_product_category=product_categories.get(icode=current_product_category_id)
	context = {
		"parent": "Entry Forms",
		"segment": "Poka Yoke - Inspection",
		"product_categories": product_categories.filter(icode__in = pyps_maps_of_awaiting_inspections_dic.keys()),
		"current_product_category": current_product_category,
		"production_lines": production_lines,
		"current_production_line": current_production_line,
		"pl_pyps_maps_of_awaiting_inspections_dic": pl_pyps_maps_of_awaiting_inspections_dic,
	}
	return render(request, 'a010/poka_yoke_inspection.html', context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Interns_or_Trainees],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def poka_yoke_inspection_additon(request):
	pyps_map = PyPsMapping.objects.get(id=request.GET.get("pyps_map_id"))
	pyps_map_inspection = PokaYokeInspections.objects.filter(pyps_map=pyps_map, inspection_due_date=pyps_map.upcoming_due_date)
	if not pyps_map_inspection.exists():
		PokaYokeInspections.objects.create(
			pyps_map = pyps_map,
			inspection_status = request.GET.get("inspection_status"),
			inspection_due_date = pyps_map.upcoming_due_date,
			inspected_user = request.user,
		)
		return JsonResponse({"submission_status":1})
	return JsonResponse({"submission_status":0})



@login_required(login_url="/accounts/login/")
def poka_yoke_tree(request, current_product_category_id):
	product_categories=serve.get_product_categories()
	current_product_category=product_categories.get(icode=current_product_category_id)
	poka_yoke_tree_pc_dict = get_poka_yoke_tree_dict_of_pc(product_category_id=current_product_category_id)
	temp_dict = {inspec_ok:0, inspec_nok:0, inspec_waiting:0}
	for pl in poka_yoke_tree_pc_dict:
		for data in poka_yoke_tree_pc_dict[pl]:
			temp_dict[data['ft']] = temp_dict[data['ft']] + data['nf']
	context = {
		"parent": "projects",
		"segment": "Poka Yoke Cards",
		"Child": "Poka Yoke - Production Lines",
		"product_categories" : product_categories,
		"current_product_category" : current_product_category,
		"poka_yoke_tree_pc_dict": get_poka_yoke_tree_dict_of_pc(product_category_id=current_product_category_id),
		"poka_yoke_tree_pc_summary_dict": {"t_ok_f":temp_dict[inspec_ok], "t_nok_f":temp_dict[inspec_nok],"t_waiting_f":temp_dict[inspec_waiting],"t_total_nf": sum(temp_dict.values())},		
	}
	return render(request, 'a010/poka_yoke_tree.html', context)


@login_required(login_url="/accounts/login/")
def poka_yoke_fruit_clusters(request, current_production_line_id):
	poka_yoke_cluster_dict = get_poka_yoke_fruit_clusters_dict(current_production_line_id)
	temp_dict = {inspec_ok:0, inspec_nok:0, inspec_waiting:0}
	for ps in poka_yoke_cluster_dict:
		for data in poka_yoke_cluster_dict[ps]:
			temp_dict[data['ft']] = temp_dict[data['ft']] + data['nf']
	context = {
		"parent": "projects",
		"segment": "Poka Yoke Cards",
		"Child": "Poka Yoke - Production Stations",
		"production_line": serve.get_icode_object(current_production_line_id),
		"poka_yoke_fruit_clusters_pl_dict": get_poka_yoke_fruit_clusters_dict(current_production_line_id),
		"poka_yoke_tree_pc_summary_dict": {"t_ok_f":temp_dict[inspec_ok], "t_nok_f":temp_dict[inspec_nok],"t_waiting_f":temp_dict[inspec_waiting],"t_total_nf": sum(temp_dict.values())},
	}
	return render(request, 'a010/poka_yoke_fruit_clusters.html', context)


@login_required(login_url="/accounts/login/")
def poka_yoke_fruits(request, current_production_station_id):
	poka_yoke_dict = get_poka_yoke_fruits_dict(current_production_station_id)
	temp_dict = defaultdict(int)
	for py in poka_yoke_dict.values():
		temp_dict[py.get('ft')] += 1
	poka_yoke_tree_pc_summary_dict = {"t_ok_f": temp_dict[True],"t_nok_f": temp_dict[False],"t_waiting_f": temp_dict[None],"t_total_nf": sum(temp_dict.values())}
	pokeyoke_data_list=[]
	for py_id,ft in poka_yoke_dict.items():
		py_maps = PyPsMapping.objects.get(poka_yoke_i=py_id,production_station_i=current_production_station_id)
		inspections_qs = PokaYokeInspections.objects.filter(
        pyps_map=py_maps,
        inspection_status__isnull=False
    	)
		if inspections_qs.exists():
			latest_insp = inspections_qs.latest('inspection_datetime')
		else:
			latest_insp = None  # handle case when no inspection exists
		pokeyoke_data_list.append((py_maps, ft, latest_insp))
	context = {
		"parent": "projects",
		"segment": "Poka Yoke Cards",
		"Child": "Poka Yoke",
		"production_station": serve.get_icode_object(current_production_station_id),
		"poka_yoke_fruits_ps_dict": get_poka_yoke_fruits_dict(current_production_station_id),		
		"poka_yoke_tree_pc_summary_dict":poka_yoke_tree_pc_summary_dict,
		"pokeyoke_data_list":pokeyoke_data_list
	}
	return render(request, 'a010/poka_yoke_fruits.html', context)
