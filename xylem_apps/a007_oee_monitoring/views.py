import json, calendar, datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Q, F, Sum, Max
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.core import paginator

import xylem.custom_messages.constants as custom_messages
from xylem_apps.a000_xylem_master import serve 
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom, view_eligibity_test
from xylem_apps.a000_xylem_master.models import Icodes

from .models import IdleEvents, OEEData, ProductionPlan, ProductionPlanMaxRef


months = [{"id": i, "name": calendar.month_name[i]} for i in range(1, 13)]
min_year = 2025
input_id_format_sub_str = "%d%m%Y_"
pp_shiftA_input_name_format = f"{input_id_format_sub_str}{serve.Shifts.ShiftA.icode}"
pp_shiftB_input_name_format = f"{input_id_format_sub_str}{serve.Shifts.ShiftB.icode}"
pp_shiftC_input_name_format = f"{input_id_format_sub_str}{serve.Shifts.ShiftC.icode}"

no_plan_txt = "No plan"
no_actual_txt = "No actual"

@login_required(login_url="/accounts/login/")
def oee_dashboard(request):
	production_lines = serve.get_production_lines_of_oee_enabled()
	production_lines_dict={}
	for i in production_lines:
		production_lines_dict[i.icode]=i.name
	context = {
		"parent": "Dashboards",
		"segment": "OEE Dashboard",
		"get_dashboard_data_url": reverse( "a007:get_dashboard_data"),
		"production_lines_dict": json.dumps(production_lines_dict),
		"oee_dashboard_color_code_dict": json.dumps(serve.OEE.dashboard_color_code_dict)
	}
	return render(request, "a007/oee_dashboard.html", context)


@login_required(login_url="/accounts/login/")
def get_dashboard_data(request):
	data = json.loads(request.body.decode("utf-8"))
	return JsonResponse(serve.get_from_background_worker_api(serve.a007_get_dashboard_dict_url+data["line_id"]).json())


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.All_plant_locations, serve.Depts.All_depts, serve.Designations.Deputy_Engineer_or_Executive],
																				   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],), redirect_url="user_access_denied")
def oee_event_response(request, current_pagination_option_id, current_page_num):
	current_pagination_option = serve.get_icode_object(current_pagination_option_id)
	user_dept_i = request.user.dept_i
	if user_dept_i in serve.OEE.depts_list or user_dept_i == serve.Depts.Development_team:

		# Process form submission (approve/reject)
		if request.method == "POST":
			event_id = request.POST.get("event_id")
			approver_response = request.POST.get("approver_response")
			idle_event = IdleEvents.objects.get(id=event_id)
			if approver_response == "1":
				idle_event.acceptance = True
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,"Event accepted successfully")
			elif approver_response == "0":
				idle_event.acceptance = False
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"Event <span style='color:#ff0000;font-weight:bold;'>rejected</span> successfully"))
			idle_event.responded_user = request.user
			idle_event.save()
			return redirect("a007:oee_event_response", current_pagination_option_id = current_pagination_option_id, current_page_num = current_page_num,)
		if user_dept_i == serve.Depts.Development_team:
			oee_events = serve.get_oee_events()
		else:
			oee_events = serve.get_oee_events(dept_i=request.user.dept_i)

		# Get unique what_id values from the filtered OEE Events
		what_ids = oee_events.values_list("icode", flat=True).distinct()

		# Filter IdleEvents based on the retrieved what_ids and where Acceptance is None
		idle_events = IdleEvents.objects.filter(Q(what_id_i_id__in=list(what_ids)) & Q(acceptance=None) & ~Q(end_time=None)).annotate(it=F("end_time") - F("start_time"))

		# Calculate and format time difference for each IdleEvents object
		for idle_event in idle_events:
			
			# Calculate hours and minutes from the timedelta object
			temp_time_secs = int(idle_event.it.total_seconds())
			mins, secs = divmod(temp_time_secs, 60)
			hrs, mins = divmod(mins, 60)
			temp_str = ""
			if not any([hrs, mins, secs]):
				temp_str = "NA"
			if hrs:
				temp_str = f"{hrs}Hr"
				if hrs>1:
					temp_str = temp_str + "s"
			if mins:
				temp_str = temp_str + f" {mins}Min"
				if mins>1:
					temp_str = temp_str + "s"
			if secs:
				temp_str = temp_str + f" {secs}Sec"
				if secs>1:
					temp_str = temp_str + "s"

			# Assign the formatted time difference to the event object
			idle_event.it_formatted = temp_str

		# Prepare context to pass data to the template
		context = {
			"parent" : "Approval",
			"segment": "OEE Events Acceptence",
			"pagination_options": serve.get_pagination_options(),
			"current_pagination_option": current_pagination_option,
			"idle_events_pagination": paginator.Paginator(idle_events.order_by('id'), current_pagination_option.description).get_page(current_page_num),
		}

		# Render the template with the provided context
		return render(request, "a007/oee_event_response.html", context)
	else:
		return redirect("user_access_denied")
	

# @login_required(login_url="/accounts/login/")
# def oee_dashboard(request):
# 	production_line_list = serve.get_production_lines_of_oee_enabled(product_category=serve.ProductCategory.seat_belt).values_list("production_line_i", flat=True)
# 	production_lines_dic={}
# 	for i in production_line_list:
# 		production_lines_dic[i.icode]=i.name
# 	context = {
# 		"parent" : "Dashboards",
# 		"segment"  : "OEE Dashboard",
# 		"get_dashboard_data_url" : reverse( "a007:get_dashboard_data" ),
# 		"production_lines_dic" : json.dumps(production_lines_dic)
# 	}
# 	return render(request, "a007/oee_dashboard.html", context)
# 	return render(request, "a007/temp.html", context)


@login_required(login_url="/accounts/login/")
def production_plan_init(request, current_product_category_id):
	dt = datetime.datetime.now()
	return redirect("a007:production_plan", current_product_category_id = current_product_category_id, current_month_id = dt.month, current_year_id = dt.year)


@login_required(login_url="/accounts/login/")
def production_plan(request, current_product_category_id, current_month_id, current_year_id):
	if current_year_id<min_year:
		return redirect("a007:production_plan_init", current_product_category_id=current_product_category_id)
	product_categories=serve.get_product_categories()
	current_product_category=product_categories.get(icode=current_product_category_id)
	dt_now = datetime.datetime.now()
	years = [{"id": year, "name": year} for year in range(min_year, dt_now.year+2)]
	current_month = months[current_month_id-1]
	current_year = {"id": current_year_id, "name": current_year_id}
	pls = serve.get_production_lines_of_oee_enabled(product_category_id=current_product_category_id)
	pp_list = []
	oee_month_data = OEEData.objects.filter(Q(date__month=current_month_id, date__year=current_year_id) & ~Q(shift=None))
	pp_month_data = ProductionPlan.objects.filter(plan_date__month=current_month_id, plan_date__year=current_year_id)
	custom_date = serve.get_custom_shift_date(dt=dt_now)
	past_month_flag = None
	if datetime.date(day=1, month=current_month_id, year=current_year_id) < dt_now.replace(day=1).date():
		past_month_flag = True
	for pl in pls:
		oee_month_data_pl = oee_month_data.filter(production_line_i=pl)
		mtd_actual = oee_month_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
		pp_month_data_pl = pp_month_data.filter(production_line_i=pl)
		month_plan = None
		last_revision = None
		mtd_plan = None
		release_flag = None
		modify_flag = None
		available_flag = None
		adherence_dict = {}
		if pp_month_data_pl.exists():
			available_flag = True
			last_revision = pp_month_data_pl.aggregate(last_revision = Max("revision"))["last_revision"]
			pp_month_data_pl_lr = pp_month_data_pl.filter(revision=last_revision)
			month_plan = pp_month_data_pl_lr.aggregate(planned_qty_month = Sum("planned_qty"))["planned_qty_month"]
			if not past_month_flag:
				modify_flag = True
				shift = serve.get_shift(dt=dt_now)
				mtd_plan = pp_month_data_pl_lr.filter(Q(plan_date__lt = custom_date) | Q(plan_date = custom_date, shift__in = shift.past_shift_list)).aggregate(planned_qty_mtd = Sum("planned_qty"))["planned_qty_mtd"]
			else:
				mtd_plan = month_plan
			if mtd_plan:
				adherence_p = serve.convert_float_with_int_possibility((mtd_actual/mtd_plan)*100,2)
				adherence_dict["percent_str"] = f"{adherence_p}%"
				adherence_dict["percent_bg_c"], adherence_dict["percent_txt_c"] = serve.get_bg_txt_color_of_percent(adherence_p)
		else:
			if not past_month_flag:
				release_flag = True
		pp_list.append({
			"production_line": pl,
			"month_plan": month_plan or "-",
			"mtd_plan": mtd_plan or "-",
			"mtd_actual": mtd_actual if available_flag else "-",
			"adherence_dict": adherence_dict or "-",
			"revision": last_revision or "-",
			"available": available_flag,
			"release": release_flag,
			"modify": modify_flag,
		})
	context = {
		"parent": "projects",
		"segment": "Production Plan",
		"current_product_category": current_product_category,
		"current_month": current_month,
		"current_year": current_year,
		"product_categories": product_categories,
		"color_code_dict": serve.color_code_dict,
		"live_present_month": current_month_id==dt_now.month and current_year_id==dt_now.year,
		"months": months,
		"years": years,
		"pp_list": pp_list
	}
	return render(request, "a007/production_plan.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.MFG, serve.Designations.Assistant_Manager],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def production_plan_release(request, production_line_id, month_id, year_id):
	production_line = serve.get_icode_object(production_line_id)
	year = year_id
	month = month_id
	dt_now = datetime.datetime.now()
	past_month_flag = None
	if datetime.date(day=1, month=month_id, year=year_id) < dt_now.replace(day=1).date():
		past_month_flag = True
	pp_release = None
	pp_month_data_pl = ProductionPlan.objects.filter(production_line_i=production_line, plan_date__month=month_id, plan_date__year=year_id)
	if pp_month_data_pl.exists():
		messages.add_message(request, messages.WARNING, 
			mark_safe(
				f"""Production plan was already exist for <b>{production_line.name} - {months[month_id-1]["name"]} {year_id}</b>, <a href="{
					reverse("a007:production_plan_modify", 
						kwargs={
							"production_line_id": production_line.icode,
							"month_id": month_id, 
							"year_id": year_id
						}
					)
				}">click here to modify<a>"""
			)
		)
		pp_release = False
	elif past_month_flag:
		messages.add_message(request, messages.WARNING,
			mark_safe(
				f"""Unable to release Production plan for past time <b>{production_line.name} - {months[month_id-1]["name"]} {year_id}</b>, <a href="{
					reverse("a007:production_plan", 
						kwargs={
							"current_product_category_id": serve.get_product_category_by_item(item_id=production_line_id).icode,
							"current_month_id": dt_now.month, 
							"current_year_id": dt_now.year
						}
					)
				}">click here to home<a>"""
			)
		)
		pp_release = False
	else:
		pp_release = True
	days_in_month = calendar.monthrange(year, month)[1]
	pp_input_data_list = []
	for day in range(1, days_in_month + 1):
		date_iter = datetime.date(year, month, day)
		pp_input_data_list.append({
			"date_str": date_iter.strftime("%d-%b-%Y"),
			"day_str": date_iter.strftime("%a"),
			"shiftA_input": {"name": date_iter.strftime(pp_shiftA_input_name_format)},
			"shiftB_input": {"name": date_iter.strftime(pp_shiftB_input_name_format)},
			"shiftC_input": {"name": date_iter.strftime(pp_shiftC_input_name_format)},
			"default_plan_status": date_iter.weekday()<6
		})
	pl_default_ct = production_line.opls_pl.default_ct
	shiftA_max = int(serve.Shifts.ShiftA.duration_time.total_seconds()/pl_default_ct)
	shiftB_max = int(serve.Shifts.ShiftB.duration_time.total_seconds()/pl_default_ct)
	shiftC_max = int(serve.Shifts.ShiftC.duration_time.total_seconds()/pl_default_ct)
	context = {
		"parent": "projects",
		"segment": "Production Plan",
		"child": "Production Plan - Release",
		"pp_release": pp_release,
		"production_line": production_line,
		"month": months[month_id-1],
		"year": {"id": year_id, "name": year_id},
		"day_max": shiftA_max + shiftB_max + shiftC_max,
		"shiftA_max": shiftA_max,
		"shiftB_max": shiftB_max,
		"shiftC_max": shiftC_max,
		"pp_revision": 1,
		"pp_input_data_list": pp_input_data_list,
	}
	return render(request, "a007/production_plan_release.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.MFG, serve.Designations.Assistant_Manager],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def production_plan_release_save(request, production_line_id, month_id, year_id):
	production_line = serve.get_icode_object(production_line_id)
	transfer_dict = json.loads(request.body.decode("utf-8"))
	year = year_id
	month = month_id
	days_in_month = calendar.monthrange(year, month)[1]
	month_start_date = datetime.date(day=1, month=month_id, year=year_id)
	ppmr_list = [
		ProductionPlanMaxRef(
			production_line_i = production_line,
			plan_date = month_start_date,
			shift = serve.Shifts.ShiftA.shift,
			production_plan_max = int(transfer_dict["shiftA_max"]),
		),
		ProductionPlanMaxRef(
			production_line_i = production_line,
			plan_date = month_start_date,
			shift = serve.Shifts.ShiftB.shift,
			production_plan_max = int(transfer_dict["shiftB_max"]),
		),
		ProductionPlanMaxRef(
			production_line_i = production_line,
			plan_date = month_start_date,
			shift = serve.Shifts.ShiftC.shift,
			production_plan_max = int(transfer_dict["shiftC_max"]),
		)
	]
	pp_list = []
	for day in range(1, days_in_month + 1):
		date_iter = datetime.date(year, month, day)
		key = date_iter.strftime(pp_shiftA_input_name_format)
		if key in transfer_dict:
			pp_list.append(
				ProductionPlan(
					production_line_i = production_line,
					plan_date = date_iter,
					shift = serve.Shifts.ShiftA.shift,
					planned_qty = transfer_dict[key],
					revision = 1,
					created_user = request.user
				)
			)
		key = date_iter.strftime(pp_shiftB_input_name_format)
		if key in transfer_dict:
			pp_list.append(
				ProductionPlan(
					production_line_i = production_line,
					plan_date = date_iter,
					shift = serve.Shifts.ShiftB.shift,
					planned_qty = transfer_dict[key],
					revision = 1,
					created_user = request.user
				)
			)
		key = date_iter.strftime(pp_shiftC_input_name_format)
		if key in transfer_dict:
			pp_list.append(
				ProductionPlan(
					production_line_i = production_line,
					plan_date = date_iter,
					shift = serve.Shifts.ShiftC.shift,
					planned_qty = transfer_dict[key],
					revision = 1,
					created_user = request.user
				)
			)
	ProductionPlan.objects.bulk_create(pp_list)
	ProductionPlanMaxRef.objects.bulk_create(ppmr_list)
	messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"Production plan released successfully for <b>{serve.get_icode_object(production_line_id).name}</b> on <b>{months[month_id-1]['name']} {year_id}</b>"))
	return JsonResponse({
		"redirect_url": reverse(
			"a007:production_plan", 
			kwargs={
				"current_product_category_id": serve.get_product_category_by_item(item_id=production_line_id).icode,
				"current_month_id": month_id, 
				"current_year_id": year_id
			}
		) 
	})


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.MFG, serve.Designations.Assistant_Manager],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def production_plan_modify(request, production_line_id, month_id, year_id):
	production_line = serve.get_icode_object(production_line_id)
	year = year_id
	month = month_id
	dt_now = datetime.datetime.now()
	past_month_flag = None
	if datetime.date(day=1, month=month_id, year=year_id) < dt_now.replace(day=1).date():
		past_month_flag = True
	pp_modify = None
	pp_month_data_pl = ProductionPlan.objects.filter(production_line_i=production_line, plan_date__month=month_id, plan_date__year=year_id)
	if past_month_flag:
		messages.add_message(request, messages.WARNING, 
			mark_safe(
				f"""Unable to modify Production plan for past time <b>{months[month_id-1]["name"]} {year_id}</b>, <a href="{
					reverse("a007:production_plan", 
						kwargs={
							"current_product_category_id": serve.get_product_category_by_item(item_id=production_line_id).icode,
							"current_month_id": dt_now.month, 
							"current_year_id": dt_now.year
						}
					)
				}">click here to home<a>"""
			)
		)
		pp_modify = False
	elif not pp_month_data_pl.exists():
		messages.add_message(request, messages.WARNING, 
			mark_safe(
				f"""Production plan was not exist for <b>{production_line.name} - {months[month_id-1]["name"]} {year_id}</b>, <a href="{
					reverse("a007:production_plan_release", 
						kwargs={
							"production_line_id": production_line.icode,
							"month_id": month_id, 
							"year_id": year_id
						}
					)
				}">click here to release plan<a>"""
			)
		)
		pp_modify = False
	else:
		pp_modify = True
	last_revision = pp_month_data_pl.aggregate(last_revision = Max("revision"))["last_revision"]
	pp_month_data_pl_lr = pp_month_data_pl.filter(revision=last_revision)
	month_plan = pp_month_data_pl_lr.aggregate(planned_qty_month = Sum("planned_qty"))["planned_qty_month"]
	custom_date = serve.get_custom_shift_date(dt=dt_now)
	shift = serve.get_shift(dt=dt_now)
	days_in_month = calendar.monthrange(year, month)[1]
	pp_input_data_list = []
	for day in range(1, days_in_month + 1):
		date_iter = datetime.date(year, month, day)
		past_shiftA_flag, past_shiftB_flag, past_shiftC_flag = None, None, None
		if date_iter < custom_date:
			past_shiftA_flag = True
			past_shiftB_flag = True
			past_shiftC_flag = True
		elif date_iter == custom_date:
			if not serve.Shifts.ShiftA.shift in shift.future_shift_list:
				past_shiftA_flag = True
			if not serve.Shifts.ShiftB.shift in shift.future_shift_list:
				past_shiftB_flag = True
			if not serve.Shifts.ShiftC.shift in shift.future_shift_list:
				past_shiftC_flag = True
		shiftA_dict = {"name": date_iter.strftime(pp_shiftA_input_name_format), "value": 0, "past_shift_flag": past_shiftA_flag, "plan_state": None}
		shiftB_dict = {"name": date_iter.strftime(pp_shiftB_input_name_format), "value": 0, "past_shift_flag": past_shiftB_flag, "plan_state": None}
		shiftC_dict = {"name": date_iter.strftime(pp_shiftC_input_name_format), "value": 0, "past_shift_flag": past_shiftC_flag, "plan_state": None}
		pp_shift_data_pl_lr = pp_month_data_pl_lr.filter(plan_date = date_iter, shift_id = serve.Shifts.ShiftA.icode)
		if pp_shift_data_pl_lr.exists():
			pp_shift_data_pl_lr_row = pp_shift_data_pl_lr.last()
			shiftA_dict["value"] = pp_shift_data_pl_lr_row.planned_qty
			shiftA_dict["plan_state"] = True
		pp_shift_data_pl_lr = pp_month_data_pl_lr.filter(plan_date = date_iter, shift_id = serve.Shifts.ShiftB.icode)
		if pp_shift_data_pl_lr.exists():
			pp_shift_data_pl_lr_row = pp_shift_data_pl_lr.last()
			shiftB_dict["value"] = pp_shift_data_pl_lr_row.planned_qty
			shiftB_dict["plan_state"] = True
		pp_shift_data_pl_lr = pp_month_data_pl_lr.filter(plan_date = date_iter, shift_id = serve.Shifts.ShiftC.icode)
		if pp_shift_data_pl_lr.exists():
			pp_shift_data_pl_lr_row = pp_shift_data_pl_lr.last()
			shiftC_dict["value"] = pp_shift_data_pl_lr_row.planned_qty
			shiftC_dict["plan_state"] = True
		pp_input_data_list.append({
			"date_str": date_iter.strftime("%d-%b-%Y"),
			"day_str": date_iter.strftime("%a"),
			"shiftA_input": shiftA_dict,
			"shiftB_input": shiftB_dict,
			"shiftC_input": shiftC_dict,
		})
	ppmr_pl = ProductionPlanMaxRef.objects.filter(production_line_i = production_line, plan_date__month = month_id, plan_date__year = year_id)
	shiftA_max, shiftB_max, shiftC_max = 0, 0, 0
	if ppmr_pl.exists():
		shiftA_max = ppmr_pl.filter(shift=serve.Shifts.ShiftA.shift).last().production_plan_max
		shiftB_max = ppmr_pl.filter(shift=serve.Shifts.ShiftB.shift).last().production_plan_max
		shiftC_max = ppmr_pl.filter(shift=serve.Shifts.ShiftC.shift).last().production_plan_max
	context = {
		"parent": "projects",	
		"segment": "Production Plan",
		"child": "Production Plan - Modify",
		"pp_modify": pp_modify,
		"production_line": production_line,
		"month": months[month_id-1],
		"year": {"id": year_id, "name": year_id},
		"month_plan": month_plan,
		"day_max": shiftA_max + shiftB_max + shiftC_max,
		"shiftA_max": shiftA_max,
		"shiftB_max": shiftB_max,
		"shiftC_max": shiftC_max,
		"pp_revision": last_revision,
		"pp_input_data_list": pp_input_data_list,
	}
	return render(request, "a007/production_plan_modify.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.MFG, serve.Designations.Assistant_Manager],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def production_plan_modify_save(request, production_line_id, month_id, year_id):
	production_line = serve.get_icode_object(production_line_id)
	transfer_dict = json.loads(request.body.decode("utf-8"))
	year = year_id
	month = month_id
	days_in_month = calendar.monthrange(year, month)[1]
	pp_list = []
	pp_month_data_pl = ProductionPlan.objects.filter(production_line_i=production_line, plan_date__month=month_id, plan_date__year=year_id)
	current_revision = pp_month_data_pl.aggregate(last_revision = Max("revision"))["last_revision"] + 1
	for day in range(1, days_in_month + 1):
		date_iter = datetime.date(year, month, day)
		key = date_iter.strftime(pp_shiftA_input_name_format)
		if key in transfer_dict:
			pp_list.append(
				ProductionPlan(
					production_line_i = production_line,
					plan_date = date_iter,
					shift = serve.Shifts.ShiftA.shift,
					planned_qty = transfer_dict[key],
					revision = current_revision,
					created_user = request.user
				)
			)
		key = date_iter.strftime(pp_shiftB_input_name_format)
		if key in transfer_dict:
			pp_list.append(
				ProductionPlan(
					production_line_i = production_line,
					plan_date = date_iter,
					shift = serve.Shifts.ShiftB.shift,
					planned_qty = transfer_dict[key],
					revision = current_revision,
					created_user = request.user
				)
			)
		key = date_iter.strftime(pp_shiftC_input_name_format)
		if key in transfer_dict:
			pp_list.append(
				ProductionPlan(
					production_line_i = production_line,
					plan_date = date_iter,
					shift = serve.Shifts.ShiftC.shift,
					planned_qty = transfer_dict[key],
					revision = current_revision,
					created_user = request.user
				)
			)
	ProductionPlan.objects.bulk_create(pp_list)
	messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"Production plan modified successfully for <b>{serve.get_icode_object(production_line_id).name}</b> on <b>{months[month_id-1]['name']} {year_id}</b>, Revision: <b>{current_revision}</b>"))
	return JsonResponse({
		"redirect_url": reverse(
			"a007:production_plan", 
			kwargs={
				"current_product_category_id": serve.get_product_category_by_item(item_id=production_line_id).icode,
				"current_month_id": month_id, 
				"current_year_id": year_id
			}
		) 
	})


@login_required(login_url="/accounts/login/")
def production_plan_view(request, production_line_id, month_id, year_id):
	production_line = serve.get_icode_object(production_line_id)
	year = year_id
	month = month_id
	dt_now = datetime.datetime.now()
	past_month_flag = None
	if datetime.date(day=1, month=month_id, year=year_id) < dt_now.replace(day=1).date():
		past_month_flag = True
	pp_view = None
	if year_id < min_year:
		messages.add_message(request, messages.WARNING, 
			mark_safe(
				f"""As the year is below {min_year}, we are unable to show Production Plan vs Actual <b>{months[month_id-1]["name"]} {year_id}</b>, <a href="{
					reverse("a007:production_plan", 
						kwargs={
							"current_product_category_id": serve.get_product_category_by_item(item_id=production_line_id).icode,
							"current_month_id": dt_now.month, 
							"current_year_id": dt_now.year
						}
					)
				}">click here to home<a>"""
			)
		)
		pp_view = False
	else:
		pp_view = True
	pp_month_data_pl = ProductionPlan.objects.filter(production_line_i=production_line, plan_date__month=month_id, plan_date__year=year_id)
	pp_view_data_list = []
	adherence_dict = {}
	custom_date = serve.get_custom_shift_date(dt=dt_now)
	days_in_month = calendar.monthrange(year, month)[1]
	oee_month_data_pl = OEEData.objects.filter(Q(date__month=month_id, date__year=year_id, production_line_i=production_line) & ~Q(shift=None))
	mtd_actual = oee_month_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
	if pp_month_data_pl.exists():
		color_code_dict = serve.color_code_dict
		last_revision = pp_month_data_pl.aggregate(last_revision = Max("revision"))["last_revision"]
		pp_month_data_pl_lr = pp_month_data_pl.filter(revision=last_revision)
		month_plan = pp_month_data_pl_lr.aggregate(planned_qty_month = Sum("planned_qty"))["planned_qty_month"]
		if not past_month_flag:
			shift = serve.get_shift(dt=dt_now)
			mtd_plan = pp_month_data_pl_lr.filter(Q(plan_date__lt = custom_date) | Q(plan_date = custom_date, shift__in = shift.past_shift_list)).aggregate(planned_qty_mtd = Sum("planned_qty"))["planned_qty_mtd"]
		else:
			mtd_plan = month_plan
		if mtd_plan:
			adherence_p = serve.convert_float_with_int_possibility((mtd_actual/mtd_plan)*100,2)
			adherence_dict["percent_str"] = f"{adherence_p}%"
			adherence_dict["percent_bg_c"], adherence_dict["percent_txt_c"] = serve.get_bg_txt_color_of_percent(adherence_p)
		temp_day_tot_planned_qty, temp_days_splited, temp_shiftA_tot_planned_qty, temp_shiftA_splited, temp_shiftB_tot_planned_qty, temp_shiftB_splited, temp_shiftC_tot_planned_qty, temp_shiftC_splited = 0, 0, 0, 0, 0, 0, 0, 0  
		for day in range(1, days_in_month + 1): 
			date_iter = datetime.date(year, month, day)
			home_dict = {"month_id": month_id, "year_id": year_id}
			day_plan = 0
			day_actual = 0
			adherence_day_dict = {}

			past_shiftA_flag, past_shiftB_flag, past_shiftC_flag = None, None, None
			if date_iter < custom_date:
				past_shiftA_flag = True
				past_shiftB_flag = True
				past_shiftC_flag = True
			elif date_iter == custom_date:
				if not serve.Shifts.ShiftA.shift in shift.future_shift_list:
					past_shiftA_flag = True
				if not serve.Shifts.ShiftB.shift in shift.future_shift_list:
					past_shiftB_flag = True
				if not serve.Shifts.ShiftC.shift in shift.future_shift_list:
					past_shiftC_flag = True

			oee_day_data_pl = oee_month_data_pl.filter(date = date_iter)
			if oee_day_data_pl.exists():
				day_actual = oee_day_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			pp_day_data_pl_lr = pp_month_data_pl_lr.filter(plan_date = date_iter)
			if pp_day_data_pl_lr.exists():
				day_plan = pp_day_data_pl_lr.aggregate(planned_qty_day = Coalesce(Sum("planned_qty"),0))["planned_qty_day"]
				temp_day_tot_planned_qty = temp_day_tot_planned_qty + day_plan
				temp_days_splited = temp_days_splited + 1
			if day_plan and (date_iter < custom_date):
				adherence_p = serve.convert_float_with_int_possibility((day_actual/day_plan)*100,2)
				adherence_day_dict["percent_str"] = f"{adherence_p}%"
				adherence_day_dict["percent_bg_c"], adherence_day_dict["percent_txt_c"] = serve.get_bg_txt_color_of_percent(adherence_p)
			else:
				day_actual = day_actual or "-"

			shift_plan = 0
			shift_actual = 0
			adherence_shift_dict = {}
			oee_shift_data_pl = oee_day_data_pl.filter(shift_id = serve.Shifts.ShiftA.icode)
			if oee_shift_data_pl.exists():
				shift_actual = oee_shift_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			pp_shift_data_pl_lr = pp_day_data_pl_lr.filter(shift_id = serve.Shifts.ShiftA.icode)
			if pp_shift_data_pl_lr.exists():
				shift_plan = pp_shift_data_pl_lr.last().planned_qty
				temp_shiftA_tot_planned_qty = temp_shiftA_tot_planned_qty + shift_plan
				temp_shiftA_splited = temp_shiftA_splited + 1
			if shift_plan and ((date_iter < custom_date) or (date_iter == custom_date and serve.Shifts.ShiftA.shift in shift.past_shift_list)):
				adherence_p = serve.convert_float_with_int_possibility((shift_actual/shift_plan)*100,2)
				adherence_shift_dict["percent_str"] = f"{adherence_p}%"
				adherence_shift_dict["percent_bg_c"], adherence_shift_dict["percent_txt_c"] = serve.get_bg_txt_color_of_percent(adherence_p)
			else:
				shift_actual = shift_actual or "-"
			shiftA_dict = {"plan": shift_plan or no_plan_txt, "actual": shift_actual or no_actual_txt, "adherence_dict": adherence_shift_dict or "-"}
			
			shift_plan = 0
			shift_actual = 0
			adherence_shift_dict = {}
			oee_shift_data_pl = oee_day_data_pl.filter(shift_id = serve.Shifts.ShiftB.icode)
			if oee_shift_data_pl.exists():
				shift_actual = oee_shift_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			pp_shift_data_pl_lr = pp_day_data_pl_lr.filter(shift_id = serve.Shifts.ShiftB.icode)
			if pp_shift_data_pl_lr.exists():
				shift_plan = pp_shift_data_pl_lr.last().planned_qty
				temp_shiftB_tot_planned_qty = temp_shiftB_tot_planned_qty + shift_plan
				temp_shiftB_splited = temp_shiftB_splited + 1
			if shift_plan and ((date_iter < custom_date) or (date_iter == custom_date and serve.Shifts.ShiftB.shift in shift.past_shift_list)):
				adherence_p = serve.convert_float_with_int_possibility((shift_actual/shift_plan)*100,2)
				adherence_shift_dict["percent_str"] = f"{adherence_p}%"
				adherence_shift_dict["percent_bg_c"], adherence_shift_dict["percent_txt_c"] = serve.get_bg_txt_color_of_percent(adherence_p)
			else:
				shift_actual = shift_actual or "-"
			shiftB_dict = {"plan": shift_plan or no_plan_txt, "actual": shift_actual or no_actual_txt, "adherence_dict": adherence_shift_dict or "-"}
			
			shift_plan = 0
			shift_actual = 0
			adherence_shift_dict = {}
			oee_shift_data_pl = oee_day_data_pl.filter(shift_id = serve.Shifts.ShiftC.icode)
			if oee_shift_data_pl.exists():
				shift_actual = oee_shift_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			pp_shift_data_pl_lr = pp_day_data_pl_lr.filter(shift_id = serve.Shifts.ShiftC.icode)
			if pp_shift_data_pl_lr.exists():
				shift_plan = pp_shift_data_pl_lr.last().planned_qty
				temp_shiftC_tot_planned_qty = temp_shiftC_tot_planned_qty + shift_plan
				temp_shiftC_splited = temp_shiftC_splited + 1
			if shift_plan and ((date_iter < custom_date) or (date_iter == custom_date and serve.Shifts.ShiftC.shift in shift.past_shift_list)):
				adherence_p = serve.convert_float_with_int_possibility((shift_actual/shift_plan)*100,2)
				adherence_shift_dict["percent_str"] = f"{adherence_p}%"
				adherence_shift_dict["percent_bg_c"], adherence_shift_dict["percent_txt_c"] = serve.get_bg_txt_color_of_percent(adherence_p)
			else:
				shift_actual = shift_actual or "-"
			shiftC_dict = {"plan": shift_plan or no_plan_txt, "actual": shift_actual or no_actual_txt, "adherence_dict": adherence_shift_dict or "-"}

			pp_view_data_list.append({
				"date_str": date_iter.strftime("%d-%b-%Y"),
				"day_str": date_iter.strftime("%a"),
				"plan": day_plan or no_plan_txt,
				"actual": day_actual or no_actual_txt,
				"adherence_dict": adherence_day_dict or "-",
				"shiftA_view": shiftA_dict,
				"shiftB_view": shiftB_dict,
				"shiftC_view": shiftC_dict,
			})
		
		ppmr_pl = ProductionPlanMaxRef.objects.filter(production_line_i = production_line, plan_date__month = month_id, plan_date__year = year_id)
		shiftA_max = ppmr_pl.filter(shift=serve.Shifts.ShiftA.shift).last().production_plan_max
		shiftB_max = ppmr_pl.filter(shift=serve.Shifts.ShiftB.shift).last().production_plan_max
		shiftC_max = ppmr_pl.filter(shift=serve.Shifts.ShiftC.shift).last().production_plan_max
		summary_table_dict = {"day": {}, "shiftA": {}, "shiftB": {}, "shiftC": {}}
		summary_table_dict["day"]["planned_qty"] = temp_day_tot_planned_qty
		summary_table_dict["day"]["splited_count"] = temp_days_splited
		summary_table_dict["day"]["planned_efficiency_in_str"] = f"{serve.convert_float_with_int_possibility((temp_day_tot_planned_qty / ((temp_shiftA_splited*shiftA_max) + (temp_shiftB_splited*shiftB_max) + (temp_shiftC_splited*shiftC_max)))*100, 2)}%"
		summary_table_dict["shiftA"]["planned_qty"] = temp_shiftA_tot_planned_qty
		summary_table_dict["shiftA"]["splited_count"] = temp_shiftA_splited
		summary_table_dict["shiftA"]["planned_efficiency_in_str"] = f"{0 if not temp_shiftA_splited else serve.convert_float_with_int_possibility((temp_shiftA_tot_planned_qty / (temp_shiftA_splited*shiftA_max))*100, 2)}%"
		summary_table_dict["shiftB"]["planned_qty"] = temp_shiftB_tot_planned_qty
		summary_table_dict["shiftB"]["splited_count"] = temp_shiftB_splited
		summary_table_dict["shiftB"]["planned_efficiency_in_str"] = f"{0 if not temp_shiftB_splited else serve.convert_float_with_int_possibility((temp_shiftB_tot_planned_qty / (temp_shiftB_splited*shiftB_max))*100, 2)}%"
		summary_table_dict["shiftC"]["planned_qty"] = temp_shiftC_tot_planned_qty
		summary_table_dict["shiftC"]["splited_count"] = temp_shiftC_splited
		summary_table_dict["shiftC"]["planned_efficiency_in_str"] = f"{0 if not temp_shiftC_splited else serve.convert_float_with_int_possibility((temp_shiftC_tot_planned_qty / (temp_shiftC_splited*shiftC_max))*100, 2)}%"
	else:
		color_code_dict = {}
		home_dict = {"month_id": dt_now.month, "year_id": dt_now.year}
		month_plan, last_revision, mtd_plan = None, None, None
		shiftA_max, shiftB_max, shiftC_max = 0, 0, 0
		summary_table_dict = {}
		for day in range(1, days_in_month + 1): 
			date_iter = datetime.date(year, month, day)
			day_actual = 0
			adherence_day_dict = {}
			oee_day_data_pl = oee_month_data_pl.filter(date = date_iter)
			if oee_day_data_pl.exists():
				day_actual = oee_day_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]

			shift_actual = 0
			oee_shift_data_pl = oee_day_data_pl.filter(shift_id = serve.Shifts.ShiftA.icode)
			if oee_shift_data_pl.exists():
				shift_actual = oee_shift_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			shiftA_dict = {"plan": "-", "actual": shift_actual or "-", "adherence_dict": "-"}
			
			shift_actual = 0
			oee_shift_data_pl = oee_day_data_pl.filter(shift_id = serve.Shifts.ShiftB.icode)
			if oee_shift_data_pl.exists():
				shift_actual = oee_shift_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			shiftB_dict = {"plan": "-", "actual": shift_actual or "-", "adherence_dict": "-"}
			
			shift_actual = 0
			oee_shift_data_pl = oee_day_data_pl.filter(shift_id = serve.Shifts.ShiftC.icode)
			if oee_shift_data_pl.exists():
				shift_actual = oee_shift_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			shiftC_dict = {"plan": "-", "actual": shift_actual or "-", "adherence_dict": "-"}

			pp_view_data_list.append({
				"date_str": date_iter.strftime("%d-%b-%Y"),
				"day_str": date_iter.strftime("%a"),
				"plan": "-",
				"actual": day_actual or "-",
				"adherence_dict": adherence_day_dict or "-",
				"shiftA_view": shiftA_dict,
				"shiftB_view": shiftB_dict,
				"shiftC_view": shiftC_dict,
			})
	context = {
		"parent": "projects",
		"segment": "Production Plan",
		"child": "Production Plan - View",
		"pp_view": pp_view,
		"color_code_dict": color_code_dict,
		"production_line": production_line,
		"month": months[month_id-1],
		"year": {"id": year_id, "name": year_id},
		"home_dict": home_dict,
		"month_plan": month_plan or "-",
		"pp_revision": last_revision or "-",
		"mtd_plan": mtd_plan or "-",
		"mtd_actual": mtd_actual or "-",
		"adherence_dict": adherence_dict or "-",
		"day_max": shiftA_max + shiftB_max + shiftC_max,
		"shiftA_max": shiftA_max,
		"shiftB_max": shiftB_max,
		"shiftC_max": shiftC_max,
		"summary_table_dict": summary_table_dict,
		"pp_view_data_list": pp_view_data_list,
	}
	return render(request, "a007/production_plan_view.html", context)


@login_required(login_url="login")
def oee_report(request):
	context = {
		"parent" : "reports",
		"segment" : "OEE Reports",
	}
	return render(request, "a007/oee_report.html", context)


@login_required(login_url="login")
def oee_report_dashboard_type(request, current_product_category_id):
	product_categories = serve.get_product_categories()
	pls = serve.get_production_lines_of_oee_enabled(product_category_id=current_product_category_id)
	context = {
		"parent": "reports",
		"segment": "OEE Reports",
		"child": "OEE Reports - Dashboard Type",  
		"production_lines": pls,
		"shifts": serve.get_shifts(),
		"current_product_category": serve.get_icode_object(current_product_category_id),
		"product_categories": product_categories       
	}    

	return render(request, "a007/oee_report_dashboard_type.html", context)


@login_required(login_url="login")
def ajax_load_oee_report_dashboard_type(request):
	production_line_ids_str = request.GET.get('production_line_ids')
	production_line_ids = list(map(int, production_line_ids_str.split(',')))
	payload = {
		"production_line_ids": production_line_ids,
		"date": request.GET.get('date'),
		"shift_id": request.GET.get('shift_id')
	}
	oee_dashboard_report_dict = serve.get_from_background_worker_api(serve.a007_get_dashboard_report_dict_url, method="POST", json=payload).json()
	# if  not oee_dashboard_report_dict:
	# 	messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, mark_safe(f"No Plan or Data is not available {date}"))
	# 	return render(request, 'msg_templates/messages.html') 	
	context = {
		"oee_dashboard_report_dict": json.dumps(oee_dashboard_report_dict),
		"oee_dashboard_color_code_dict": json.dumps(serve.OEE.dashboard_color_code_dict)
	}
	return render(request, 'a007/ajax_load_oee_report_dashboard_type.html', context)