import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models import Q
from django.template.loader import render_to_string
from django.core import paginator

import xylem.custom_messages.constants as custom_messages
from xylem_apps.a000_xylem_master.models import PatrolCheckSheets
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom, view_eligibity_test
from xylem_apps.a000_xylem_master import serve 

from xylem_apps.a000_xylem_master.forms import PlMPnSelectionForm

from .forms import PlDSSelectionForm
from .models import InspectionData, InspectionDataDuplet

# Create your views here.
@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.All_designations],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_inspection_selection(request):
	form=PlMPnSelectionForm(request.POST or None)
	if request.method == "POST":
		if form.is_valid():
			production_line = form.cleaned_data["production_line"]
			part_number = form.cleaned_data["part_number"]
			qa_pcs_id = PatrolCheckSheets.objects.filter(production_line_i=production_line, part_number_i=part_number, alive_flag=True).first().id
			return redirect("a005:qa_patrol_inspection", qa_pcs_id=qa_pcs_id)
		else:
			error_msg=""
			for field, errors in form.errors.as_data().items():
				error_msg= error_msg+";".join(errors[0].messages)
			messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
			return redirect("a005:qa_patrol_inspection_selection")
	context = {
		"parent": "Entry Forms",
		"segment": "QA Patrol - Inspection",
		"child": "QA Patrol Inspection - Checksheet Selection",
		"form_plpn_selection": form,
		# "qa_pcs": qa_pcs,
	}	
	return render(request, "a005/qa_pc_inspection_selection.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.All_designations],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_inspection(request, qa_pcs_id):
	qa_pcs = PatrolCheckSheets.objects.get(id=qa_pcs_id)
	context = {
		"parent": "Entry Forms",
		"segment": "QA Patrol - Inspection",
		"child": "QA Patrol Check Sheet - Inspection",
		"operator_input_element_name": serve.qa_pcs_operator_input_element_name,
		"operator_input_elements_max": serve.qa_pcs_operator_input_elements_max,
		"qa_pcs_inspection_input_element_name": serve.qa_pcs_inspection_input_element_name,
		"qa_pcs": qa_pcs,
	}
	if request.method == "POST" and qa_pcs_id:
		temp_str = ""
		temp_dict = {}
		temp_dict["patrol_checksheet"] = qa_pcs
		temp_dict["inspected_by"] = request.user

		# Operator Inputs
		for i in range(serve.qa_pcs_operator_input_elements_max):
			temp_str = serve.qa_pcs_operator_input_element_name + str(i)
			if temp_str in request.POST:
				temp_dict[temp_str] = serve.get_user_object(request.POST[temp_str])

		# Inspection Inputs
		for i in range(serve.qa_pcs_inspection_input_elements_max):
			temp_str = serve.qa_pcs_inspection_input_element_name + str(i)
			if temp_str in request.POST:
				temp_dict[temp_str] = request.POST[temp_str]
		inspec_obj = InspectionData.objects.create(**temp_dict)
		
		temp_dict = {}

		# Inspection Duplet Inputs
		for i in range(serve.qa_pcs_inspection_input_elements_max):
			temp_str = serve.qa_pcs_inspection_input_element_name + "_S02" + str(i)
			if temp_str in request.POST:
				temp_dict[serve.qa_pcs_inspection_input_element_name + str(i)] = request.POST[temp_str]
		InspectionDataDuplet.objects.create(inspection_data_ref=inspec_obj, **temp_dict)
	
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"Inspection data saved successfully, <a href='{reverse('a005:qa_patrol_inspection_single_view', args=(inspec_obj.id,))}'><u> Ref ID: {'-'.join([serve.xylem_code,serve.an_qa_patrol_check,str(inspec_obj.id)])} </u></a>"))
		return redirect("a005:qa_patrol_inspection", qa_pcs_id=qa_pcs.id)
	return render(request, "a005/qa_pc_inspection.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.All_designations],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_inspection_single_view(request, qa_insp_id):
	qa_insp = InspectionData.objects.get(id=qa_insp_id)
	ajax_context = get_context_for_ajax_inspection_table(qa_insp=qa_insp)
	context = {
		"parent": "Entry Forms",
		"segment": "QA Patrol - Inspection",
		"child": "QA Patrol Inspection - Single view ",
		"qa_pcs": qa_insp.patrol_checksheet,
		"inspection_table_html": render_to_string("a005/ajax_inspection_table.html", ajax_context),
		"ref_id": ajax_context["ref_id"],
	}
	return render(request, "a005/qa_pc_inspection_single_view.html", context)


def get_inspections(production_line, date, shift):
	qa_pcss = list(serve.get_qa_patrol_checksheets_of_pl(production_line = production_line))
	return InspectionData.objects.filter(patrol_checksheet__in=qa_pcss, inspec_datetime__gte=shift.start_date_time(date), inspec_datetime__lt=shift.ns_start_date_time(date)).order_by("inspec_datetime")


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_inspection_approval(request, current_pagination_option_id, current_page_num):
	current_pagination_option = serve.get_icode_object(current_pagination_option_id)
	new_inspections = InspectionData.objects.filter(response = None)
	context = {
        "parent": "Approval",
		"segment": "Patrol Inspections",
		"app_name": serve.an_qa_patrol_check,
		"pagination_options": serve.get_pagination_options(),
		"current_pagination_option": current_pagination_option,
		"new_inspections_pagination": paginator.Paginator(new_inspections.order_by('-inspec_datetime'), current_pagination_option.description).get_page(current_page_num),		       
    }
	return render(request, 'a005/qa_pc_inspection_approval.html', context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_inspection_approval_view(request, current_pagination_option_id, current_page_num, qa_insp_id):
	qa_insp = InspectionData.objects.get(id=qa_insp_id)
	if request.method == "POST":
		response = request.POST.get("approver_response")
		if qa_insp.response is None: 
			if response == '1':
				qa_insp.response = True
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,
                                     mark_safe(f"Inspection Form <a>{'-'.join([serve.xylem_code,serve.an_qa_patrol_check,str(qa_insp.id)])} </a> is <b>approved</b> successfully"))
			else:
				qa_insp.response = False
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,
                                     mark_safe(f"Inspection Form <a>{'-'.join([serve.xylem_code,serve.an_qa_patrol_check,str(qa_insp.id)])} </a> is <span style='color:#ff0000;font-weight:bold;'>rejected</span> successfully"))
			qa_insp.responded_user = request.user
			qa_insp.response_datetime = timezone.now()
			qa_insp.save()
		return redirect("a005:qa_patrol_inspection_approval", current_pagination_option_id = current_pagination_option_id, current_page_num = current_page_num,)
	inspection_table_html = ""
	if qa_insp.response is None:
		inspection_table_html = render_to_string("a005/ajax_inspection_table.html", get_context_for_ajax_inspection_table(qa_insp=qa_insp))
	else:
		messages.warning(request, f"This inspection was already approved by {qa_insp.responded_user}")
	context = {
		"parent": "Approval",
		"segment": "Patrol Inspections",
		"child": "Patrol Inspections - Approval View",
		"inspection_table_html": inspection_table_html,
		"current_pagination_option_id": current_pagination_option_id,
		"current_page_num": current_page_num,
	}
	return render(request,'a005/qa_pc_inspection_approval_view.html', context)


@login_required(login_url="login")
def qa_patrol_report_selection(request):
	form = PlDSSelectionForm(request.POST or None)
	if request.method == "POST":
		if form.is_valid():
			production_line = form.cleaned_data["production_line"]
			date = form.cleaned_data["date"]
			shift = form.cleaned_data["shift"]
			if shift.icode == serve.IcodeSplitup.icode_shiftA:
				shift = serve.Shifts.ShiftA
			elif shift.icode == serve.IcodeSplitup.icode_shiftB:
				shift = serve.Shifts.ShiftB
			else:
				shift = serve.Shifts.ShiftC
			inspections = get_inspections(production_line=production_line, date=date, shift=shift)
			if inspections.exists():
				return redirect(
					"a005:qa_patrol_report_view", 
					ref_qa_insp_id = inspections.first().id,
				)
			else:
				messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, mark_safe(f"No Inspection Data found for the {production_line.name} on {date} {shift.name}"))
				return redirect("a005:qa_patrol_report_selection")
		else:
			error_msg=""
			for field, errors in form.errors.as_data().items():
				error_msg= error_msg+";".join(errors[0].messages)
			messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
			return redirect("a005:qa_patrol_report_selection")
	context = {
		"parent": "reports",
		"segment": "QA Patrol Report",
		"child": "QA Patrol Report - Selection",
		"form_plds_selection": form,
	}
	return render(request, "a005/qa_patrol_report_selection.html", context)


@login_required(login_url="login")
def qa_patrol_report_view(request, ref_qa_insp_id):
	qa_insp = InspectionData.objects.get(id=ref_qa_insp_id)
	dt = qa_insp.inspec_datetime
	production_line = qa_insp.patrol_checksheet.production_line_i
	shift = serve.get_shift(dt)
	date = serve.get_custom_shift_date(dt)
	inspections = get_inspections(production_line=production_line, date=date, shift=shift).values_list('id', flat=True)
	context = {
		"parent": "reports",
		"segment": "QA Patrol Report",
		"child": "QA Patrol Report - View",
		"production_line": production_line,
		"date": date,
		"shift": shift,
		"inspections": inspections,
	}
	return render(request,'a005/qa_patrol_report_view.html', context)



def get_context_for_ajax_inspection_table(qa_insp = None, qa_insp_id = None):
	if qa_insp is None:
		qa_insp = InspectionData.objects.get(id=qa_insp_id)
	dt = qa_insp.inspec_datetime
	inspec_by = serve.get_user_display_format(user=qa_insp.inspected_by)
	responded_user = serve.na_str
	response_datetime = serve.na_str
	if qa_insp.response is None:
		response = serve.st_pend_str
	elif qa_insp.response:
		response = serve.st_appr_str
		responded_user = serve.get_user_display_format(user=qa_insp.responded_user)
		response_datetime = qa_insp.response_datetime
	else:
		response = serve.st_rej_str
		responded_user = serve.get_user_display_format(user=qa_insp.responded_user)
		response_datetime = qa_insp.response_datetime
	shift = serve.get_shift(dt)
	date = serve.get_custom_shift_date(dt)
	input_values_dict = {}
	inspections = list(get_inspections(production_line=qa_insp.patrol_checksheet.production_line_i, date=date, shift=shift).values_list('id', flat=True))
	for i in range(serve.qa_pcs_operator_input_elements_max):
		elem_name = f"{serve.qa_pcs_operator_input_element_name}{i}"
		elem_val = getattr(qa_insp, elem_name)
		if not elem_val is None:
			input_values_dict[elem_name] = serve.get_user_display_format(user=elem_val)
	for i in range(serve.qa_pcs_inspection_input_elements_max):
		elem_name = f"{serve.qa_pcs_inspection_input_element_name}{i}"
		elem_val = getattr(qa_insp, elem_name)
		if not elem_val is None:
			input_values_dict[elem_name] = elem_val
	
	input_values_duplet_dict = {}
	if InspectionDataDuplet.objects.filter(inspection_data_ref=qa_insp).exists():
		qa_insp_duplet_obj = InspectionDataDuplet.objects.get(inspection_data_ref=qa_insp)
		for i in range(serve.qa_pcs_inspection_input_elements_max):
			elem_name = f"{serve.qa_pcs_inspection_input_element_name}{i}"
			elem_val = getattr(qa_insp_duplet_obj, elem_name)
			if not elem_val is None:
				input_values_duplet_dict[elem_name] = elem_val
	
	return {
		"qa_pcs": qa_insp.patrol_checksheet,
		"inspec_datetime": dt,
		"shift": shift.name,
		"current_inspec": inspections.index(qa_insp.id)+1,
		"total_inspec": len(inspections),
		"inspected_by": inspec_by,
		"approval_status": response,
		"responded_user": responded_user,
		"response_datetime": response_datetime,
		"inspection_data": json.dumps(input_values_dict),
		"inspection_data_duplet": json.dumps(input_values_duplet_dict),
		"ref_id": "-".join([serve.xylem_code, serve.an_qa_patrol_check, str(qa_insp.id)]),
	}


@login_required(login_url="login")
def ajax_get_inspection_table(request):
	return render(request, "a005/ajax_inspection_table.html", get_context_for_ajax_inspection_table(qa_insp_id=request.GET.get('inspection_id')))