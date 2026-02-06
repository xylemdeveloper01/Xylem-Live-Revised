import os, json, datetime, random
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.views.generic import CreateView, TemplateView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q, F, Sum, When, Case, Value, Avg
from django.template.loader import render_to_string
from django.core import paginator
from django.http import JsonResponse


import xylem.custom_messages.constants as custom_messages
from xylem.settings import XYLEM_MODE, XYLEM_MODE_DIC
from . import serve
from .forms import RegistrationForm, LoginForm, UserPasswordChangeForm, EditUserProfileForm, UserPasswordResetForm, UserSetPasswordForm,\
    ProductCategoryForm, TechnologyCreationForm, ProductionLineCreationForm, ProductionStationCreationForm, ModelCreationForm, PartNumberCreationForm, ChildPartNumberCreationForm,\
	RejectionReasonCreationForm, ToolCreationForm, PokaYokeCreationForm, PlMPnSelectionForm,\
	PcPlMappingForm, PnMTMappingForm, PnCpnMappingForm, PnPrlPsMappingForm,\
	TPsMappingForm, PyPsMappingForm,\
	ToolLifeParamEditForm, ToolPartNumberMapEditForm, ToolImageEditForm, OEEEventsForm, PnDrawingForm
from .tests import user_passes_test_custom, view_eligibity_test
from .models import Icodes, UserProfile, UserPreventedMails, PcPlMapping, PnMTMapping, PnCpnMapping, PnPrlPsMapping, PnPrlCtData, TPsMapping, PyPsMapping,\
	TPsmapPnExMapping, OeDMapping, PatrolCheckSheets, WorkflowForms,workflowSectionDepartmentMapping,WorkflowFormSections,WorkflowFormApprover,WorkflowApproverMapping,\
	PnDrawings


# Components
@login_required(login_url="/accounts/login/")
def bc_button(request):
		context = {
			"parent": "basic_components",
			"segment": "button"
		}
		return render(request, "pages/components/bc_button.html", context)


@login_required(login_url="/accounts/login/")
def bc_badges(request):
		context = {
			"parent": "basic_components",
			"segment": "badges"
		}
		return render(request, "pages/components/bc_badges.html", context)


@login_required(login_url="/accounts/login/")
def bc_breadcrumb_pagination(request):
		context = {
			"parent": "basic_components",
			"segment": "breadcrumbs_&_pagination"
		}
		return render(request, "pages/components/bc_breadcrumb-pagination.html", context)


@login_required(login_url="/accounts/login/")
def bc_collapse(request):
		context = {
			"parent": "basic_components",
			"segment": "collapse"
		}
		return render(request, "pages/components/bc_collapse.html", context)


@login_required(login_url="/accounts/login/")
def bc_tabs(request):
	context = {
		"parent": "basic_components",
		"segment": "navs_&_tabs"
	}
	return render(request, "pages/components/bc_tabs.html", context)


@login_required(login_url="/accounts/login/")
def bc_typography(request):
	context = {
		"parent": "basic_components",
		"segment": "typography"
	}
	return render(request, "pages/components/bc_typography.html", context)


@login_required(login_url="/accounts/login/")
def icon_feather(request):
	context = {
		"parent": "basic_components",
		"segment": "feather_icon"
	}
	return render(request, "pages/components/icon-feather.html", context)


# Forms and Tables
@login_required(login_url="/accounts/login/")
def form_elements(request):
	context = {
		"parent": "form_components",
		"segment": "form_elements"
	}
	return render(request, "pages/form_elements.html", context)


@login_required(login_url="/accounts/login/")
def basic_tables(request):
	context = {
		"parent": "tables",
		"segment": "basic_tables"
	}
	return render(request, "pages/tbl_bootstrap.html", context)


# Chart and Maps
@login_required(login_url="/accounts/login/")
def morris_chart(request):
	context = {
		"parent": "chart",
		"segment": "morris_chart"
	}
	return render(request, "pages/chart-morris.html", context)


@login_required(login_url="/accounts/login/")
def google_maps(request):
	context = {
		"parent": "maps",
		"segment": "google_maps"
	}
	return render(request, "pages/map-google.html", context)


# Authentication
class UserRegistrationView(CreateView):
	template_name = "accounts/auth-registration.html"
	form_class = RegistrationForm
	success_url = "/accounts/user-registration-done/"


class UserLoginView(LoginView):
	template_name = "accounts/auth-signin.html"
	form_class = LoginForm


class UserPasswordResetView(PasswordResetView):
	template_name = "accounts/auth-reset-password.html"
	form_class = UserPasswordResetForm


class UserPasswrodResetConfirmView(PasswordResetConfirmView):
	template_name = "accounts/auth-password-reset-confirm.html"
	form_class = UserSetPasswordForm


class UserPasswordChangeView(PasswordChangeView):
	template_name = "accounts/auth-change-password.html"
	form_class = UserPasswordChangeForm


class UserRegistrationDoneView(TemplateView):
  	template_name = "accounts/auth-registration-done.html"
	  

class UserApprovalAwaitView(TemplateView):
  	template_name = "accounts/auth-user-approval-await.html"


class UserAccessDeniedView(TemplateView):
  	template_name = "accounts/autn-user-access-denied.html"


class UnderDevelopmentView(TemplateView):
  	template_name = "pages/under-development.html"


def logout_view(request):
	logout(request)
	return redirect("/accounts/login/")


@login_required(login_url="/accounts/login/")
def profile(request):
	context = {
		"segment": "profile",
	}
	return render(request, "accounts/auth-user-profile-view.html", context)


@login_required(login_url="/accounts/login/")
def edit_user_profile_view(request, user_id): 
	user_profile = UserProfile.objects.get(id=user_id)
	form = EditUserProfileForm(request.POST or None, instance=user_profile)
	if request.method == 'POST':
		if form.is_valid():         
			user_profile.save()        
			messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, "Profile updated successfully")
			return redirect('profile')                          
		else:
			error_msg=""
			for field, errors in form.errors.as_data().items():
				error_msg= error_msg+";".join(errors[0].messages)
			messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
			return redirect("edit_user_profile", user_id=user_id)
	else:
		form = EditUserProfileForm(instance=user_profile)
	context = {
		"segment": "profile",
		"form": form,
		"user_profile": user_profile
	}
	return render(request, "accounts/auth-user-profile-edit.html", context)


@login_required(login_url="/accounts/login/")
def manage_mails(request):
	mails = serve.get_mails_of_user(user=request.user)
	if request.method == "POST":
		for mail in mails:
			status = request.POST.get(f'{mail.icode}')
			if not status == "on":
				if not UserPreventedMails.objects.filter(user=request.user, mail_i=mail).exists():
					UserPreventedMails.objects.create(user=request.user, mail_i=mail)
			else:
				UserPreventedMails.objects.filter(user=request.user, mail_i=mail).delete()
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, "Mail notification settings updated successfully")
		return redirect('manage_mails')	
	context = {
		"segment": "Mails",
		"mails": mails, 
	}
	return render(request, "accounts/auth-user-manage-mails.html", context)


@login_required(login_url="/accounts/login/")
def sample_page(request):
	context = {
		"segment": "sample_page",
	}
	return render(request, "pages/sample-page.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.All_depts, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def new_users_handle(request, current_pagination_option_id, current_page_num):
	current_pagination_option = serve.get_icode_object(current_pagination_option_id)
	if request.method == "POST":
		temp_list=request.POST.get("approver_response").split(":")
		new_user_obj = UserProfile.objects.get(pk=temp_list[1])
		if new_user_obj.is_active==None:
			if temp_list[0]=="1":
				new_user_obj.is_active = True
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The new user <b>{serve.get_user_display_format(user=new_user_obj)}</b> is <b>approved</b> successfully"))
			else:
				new_user_obj.is_active = False
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, 
					mark_safe(f"The new user <b>{serve.get_user_display_format(user=new_user_obj)}</b> is <span style='color:#ff0000;font-weight:bold;'>rejected</span> successfully"))
			new_user_obj.responded_by = request.user
			new_user_obj.save()
		else:
			messages.info(request, "Response for this new user is given already")
		return redirect("new_users_handle", current_pagination_option_id = current_pagination_option_id, current_page_num = current_page_num,)
	
	if request.user.designation_i==serve.Designations.President:
		new_users = UserProfile.objects.filter(is_active=None,)
	else:
		new_users = UserProfile.objects.filter(is_active=None, 
						plant_location_i=request.user.plant_location_i, 
						dept_i=request.user.dept_i,
						designation_i__lt=request.user.designation_i)
	context = {
		"parent" : "Approval",
		"segment" : "New Users",
		"pagination_options": serve.get_pagination_options(),
		"current_pagination_option": current_pagination_option,
		"new_users_pagination": paginator.Paginator(new_users.order_by('id'), current_pagination_option.description).get_page(current_page_num),
	}
	return render(request, "pages/new-users-handle.html", context)


@login_required(login_url="login")	
def dept_org_chart(request, dept_id):
	if request.method == "POST":
		temp_list = request.POST.get("user_response").split(":")
		user_obj = UserProfile.objects.get(pk=temp_list[1])
		if user_obj.is_active==True:
			if temp_list[0]=="0":				
				user_obj.is_active = False
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, 
					mark_safe(f"The user <b>{serve.get_user_display_format(user=user_obj)}</b> is <span style='color:#ff0000;font-weight:bold;'>Deactivated</span> successfully"))
			user_obj.responded_by = request.user
			user_obj.save()
		else:
			messages.info(request, "This user is deactivated already")
		return redirect("dept_org_chart", dept_id)
	current_dept_users = UserProfile.objects.filter(dept_i_id=dept_id, is_active=True)	
	filtered_dept_users = {
		serve.get_icode_object(designation).name: current_dept_users.filter(designation_i=designation) 
		for designation in current_dept_users.values_list("designation_i", flat=True).distinct().order_by('-designation_i')
	}
	if not filtered_dept_users	:  
		messages.info(request, "No users registered in this department")

	context = {		
		"segment": "Department Organization Chart",
		"serve_depts": serve.Depts,
		"serve_desigantions": serve.Designations,
		"depts": serve.get_depts(),
		"current_dept": serve.get_icode_object(dept_id),
		"filtered_dept_users": filtered_dept_users,
	}
	return render(request, "pages/dept_org_chart.html", context)


@login_required(login_url="/accounts/login/")
def dp_part(request, current_product_category_id):
	form_product_category=ProductCategoryForm()
	form_tech=TechnologyCreationForm()
	form_prod_line=ProductionLineCreationForm()
	form_prod_station=ProductionStationCreationForm()
	form_model=ModelCreationForm()
	form_part_number=PartNumberCreationForm()
	form_cp_number=ChildPartNumberCreationForm()
	form_rejection_reason=RejectionReasonCreationForm()
	form_tool=ToolCreationForm()
	form_poka_yoke=PokaYokeCreationForm()
	form_pcpl_map=PcPlMappingForm()
	form_pnmt_map=PnMTMappingForm()
	form_pncpn_map=PnCpnMappingForm()
	form_pnprlps_map=PnPrlPsMappingForm()
	form_tps_map=TPsMappingForm()
	form_pyps_map=PyPsMappingForm()
	product_categories=serve.get_product_categories()
	current_product_category=product_categories.get(icode=current_product_category_id)
	prod_line_avl=serve.get_production_lines(product_category_id=current_product_category_id)
	prod_line_stations_avl_dic = {}
	for prod_line in prod_line_avl:
		prod_line_stations_avl_dic[prod_line]=serve.get_production_stations(production_line=prod_line)
	tools_avl_dic = {}
	for tool_type in serve.get_tool_types():
		tools_avl_dic[tool_type] = serve.get_tools(product_category_id=current_product_category_id, tool_type=tool_type)
	context = {
		"parent" : "Data Panel",
		"segment" : "dp_part",
		"current_product_category" : current_product_category,
		"product_categories" : product_categories,
		"form_product_category" : form_product_category,
		"form_tech" : form_tech,
		"form_prod_line" : form_prod_line,
		"form_prod_station": form_prod_station,
		"form_model": form_model,
		"form_part_number": form_part_number,
		"form_cp_number": form_cp_number,
		"form_rejection_reason" : form_rejection_reason,
		"form_tool" : form_tool,
		"form_poka_yoke" : form_poka_yoke,
		"tech_avl": serve.get_product_technologies(product_category_id=current_product_category_id),
		"prod_line_stations_avl_dic": prod_line_stations_avl_dic,
		"product_models_avl": serve.get_product_models(product_category_id=current_product_category_id),
		"part_numbers_avl": serve.get_part_numbers(product_category_id=current_product_category_id),
		"cp_numbers_avl": serve.get_child_part_numbers(product_category_id=current_product_category_id),
		"rejection_reasons_avl": serve.get_rejection_reasons(product_category_id=current_product_category_id),
		"tool_fixtures": serve.Others.tool_fixtures,
		"tools_avl_dic": tools_avl_dic,
		"poka_yokes_avl": serve.get_poka_yokes(product_category_id=current_product_category_id),
		"form_pcpl_map": form_pcpl_map,
		"form_pnmt_map": form_pnmt_map,
		"form_pncpn_map": form_pncpn_map,
		"form_pnprlps_map": form_pnprlps_map,
		"form_tps_map" : form_tps_map,
		"form_pyps_map" : form_pyps_map,
	}
	return render(request, "pages/data_panel/dp_part.html", context)


@login_required(login_url="/accounts/login/")
def dp_qa_patrol(request, current_product_category_id, current_checksheet_status_type_id):
    form_plpn_selection=PlMPnSelectionForm()
    product_categories=serve.get_product_categories()
    checksheets_status_types=serve.get_checksheets_status_types()
    current_product_category=product_categories.get(icode=current_product_category_id)
    current_checksheet_status_type=checksheets_status_types.get(icode=current_checksheet_status_type_id)
    if current_checksheet_status_type == serve.Others.active_checksheets_option:
        alive_flag = True
    elif current_checksheet_status_type == serve.Others.deactivated_checksheets_option:
        alive_flag = False
    else:
        alive_flag = None
    prod_line_qa_pcs_avl = serve.get_production_lines(product_category_id=current_product_category_id)
    pl_pn_qa_pcs_avl_dic = {}
    pl_pn_wo_cs_dic = {}
    total_pn_wo_cs_count = 0
    prod_lines = serve.get_production_lines(product_category_id=current_product_category_id)
    for prod_line in prod_lines:
        pn_in_pl_cs = set(serve.get_part_numbers_of_pl_qa_pcs(production_line=prod_line, alive_flag=True))
        pn_in_pl = set(serve.get_part_numbers_of_pl(production_line_id=prod_line.icode))
        pn_wo_cs_in_pl = pn_in_pl - pn_in_pl_cs
        if pn_wo_cs_in_pl:
            pl_pn_wo_cs_dic[prod_line] = list(pn_wo_cs_in_pl)
        total_pn_wo_cs_count = 0
        for pns in pl_pn_wo_cs_dic.values():
            total_pn_wo_cs_count += len(pns)
    for prod_line in prod_line_qa_pcs_avl:
        pl_pn_qa_pcs_avl_dic[prod_line] = serve.get_qa_patrol_checksheets_of_pl(production_line=prod_line, alive_flag=alive_flag)           
    context = {
        "parent" : "Data Panel",
        "segment" : "dp_qa_patrol",
        "current_product_category" : current_product_category,
        "current_checksheet_status_type" : current_checksheet_status_type,
        "product_categories" : product_categories,
        "checksheets_status_types" : checksheets_status_types,
        "form_plpn_selection" : form_plpn_selection,
        "pl_pn_qa_pcs_avl_dic": pl_pn_qa_pcs_avl_dic,
        "pl_pn_wo_cs_dic": pl_pn_wo_cs_dic,
        "total_pn_wo_cs_count": total_pn_wo_cs_count,
    }
    return render(request, "pages/data_panel/dp_qa_patrol/dp_qa_patrol.html", context)


@login_required(login_url="login")
def dp_oee_event(request, current_dept_id):
	current_dept_i = serve.get_icode_object(current_dept_id)
	user_dept_i = request.user.dept_i
	od_list = serve.OEE.depts_list
	if not current_dept_i in od_list:
		current_dept_i = od_list[0]
	if user_dept_i in od_list:
		map_enabled = True
	else:
		map_enabled = False
	oee_events_of_dept = serve.get_oee_events(dept_i = current_dept_i)
	context = {
		"parent": "Data Panel",
		"segment": "dp_oee_event",
		"current_dept_i": current_dept_i,
		"depts_for_oee_list": od_list,
		"oee_events_of_dept": oee_events_of_dept,
	}
	if map_enabled:
		context["user_dept_i"] = user_dept_i
		context["form"] = OEEEventsForm()
	return render(request, "pages/data_panel/dp_oee_events.html", context)


@login_required(login_url="login")
def dp_workflows(request,current_workflow_status_type_id):
	workflow_status_types=serve.get_worflows_status_types()
	current_workflow_status_type=workflow_status_types.get(icode=current_workflow_status_type_id)
	if current_workflow_status_type == serve.Others.active_workflows_option:
		status_flag = 1
	elif current_workflow_status_type == serve.Others.deactivated_workflows_option:
		status_flag = 0
	elif current_workflow_status_type == serve.Others.holded_workflows_option:
		status_flag = 2
	else:
		status_flag = None
	wf_avl = serve.get_workflows_fms(status_flag=status_flag)
	context = {
		"parent": "Data Panel",
		"segment": "Workflows",
		"current_workflow_status_type" : current_workflow_status_type,
		"workflow_status_types" : workflow_status_types,
		"wf_avl" : wf_avl,
	}
	return render(request, "pages/data_panel/dp_workflows/dp_workflows.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def product_category_addition(request, current_product_category_id):
	form=ProductCategoryForm(request.POST)
	if form.is_valid():
		product_category_name=form.cleaned_data["product_category_name"] 
		serve.create_product_category(product_category_name=product_category_name)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The product category <b>{product_category_name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def tech_addition(request, current_product_category_id):
	form=TechnologyCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		tech_name = form.cleaned_data["technology_name"] 
		serve.create_technology(product_category, technology_name=tech_name)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The technology <b>{tech_name}</b> for <b>{product_category.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def prod_line_addition(request, current_product_category_id):
	form=ProductionLineCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		production_line_name = form.cleaned_data["production_line_name"] 
		serve.create_production_line(product_category, production_line_name=production_line_name)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The production line <b>{production_line_name}</b> for <b>{product_category.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)

	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)

	
@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def prod_station_addition(request, current_product_category_id):
	form=ProductionStationCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		production_line=form.cleaned_data["production_line"]
		production_station_name=form.cleaned_data["production_station_name"] 
		serve.create_production_station(product_category, production_line=production_line, production_station_name=production_station_name)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The production station <b>{production_station_name}</b> for <b>{product_category.name}:{production_line.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)

	
@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def model_addition(request, current_product_category_id):
	form=ModelCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		model_name = form.cleaned_data["model_name"] 
		serve.create_model(product_category, model_name=model_name)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The model <b>{model_name}</b> for <b>{product_category.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def part_number_addition(request, current_product_category_id):
	form=PartNumberCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		part_number_name = form.cleaned_data["part_number_name"]
		part_number_desc = form.cleaned_data["part_number_desc"]
		serve.create_part_number(product_category, part_number_name=part_number_name, part_number_desc=part_number_desc)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The part number <b>{part_number_name} [{part_number_desc}]</b> for <b>{product_category.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)

@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def cp_number_addition(request, current_product_category_id):
	form=ChildPartNumberCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		child_part_number_name = form.cleaned_data["child_part_number_name"] 
		child_part_number_desc = form.cleaned_data["child_part_number_desc"]
		serve.create_child_part_number(product_category, child_part_number_name=child_part_number_name, child_part_number_desc=child_part_number_desc)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The cp_number <b>{child_part_number_name} [{child_part_number_desc}]</b> for <b>{product_category.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	

@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def rejection_reason_addition(request, current_product_category_id):
	form=RejectionReasonCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		rejection_reason_name = form.cleaned_data["rejection_reason_name"] 
		serve.create_rejection_reason(product_category, rejection_reason_name=rejection_reason_name)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The rejection reason <b>{rejection_reason_name}</b> for <b>{product_category.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def tool_addition(request, current_product_category_id):
	form=ToolCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		tool_type = form.cleaned_data["tool_type"]
		tool_name = form.cleaned_data["tool_name"] 
		serve.create_tool(product_category, tool_type=tool_type, tool_name=tool_name)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The {tool_type.name} <b>{tool_name}</b> for <b>{product_category.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	

@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def poka_yoke_addition(request, current_product_category_id):
	form=PokaYokeCreationForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		poka_yoke_name = form.cleaned_data["poka_yoke_name"] 
		serve.create_poka_yoke(product_category, poka_yoke_name=poka_yoke_name)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The <b>{poka_yoke_name}</b> for <b>{product_category.name}</b> is added successfully"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	

@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def pcpl_mapping(request, current_product_category_id):
	form=PcPlMappingForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		plant_location = form.cleaned_data["plant_location"]
		PcPlMapping.objects.create(
			product_category_i=product_category,
			plant_location_i=plant_location,
			mapped_by=request.user,
		)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The mapping of <b>{product_category.name}, {plant_location.name}</b> is successful"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	

@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def pnmt_mapping(request, current_product_category_id):
	form=PnMTMappingForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		part_number = form.cleaned_data["part_number"]
		model = form.cleaned_data["model"]
		technology = form.cleaned_data["technology"]
		PnMTMapping.objects.create(
			part_number_i = part_number,
			model_i=model,
			technology_i=technology,
			mapped_by=request.user,
		)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The mapping of <b>{part_number.name}, {model.name}, {technology.name}</b> for <b>{product_category.name}</b> is successful"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	

@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def pncpn_mapping(request, current_product_category_id):
	form=PnCpnMappingForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		part_number = form.cleaned_data["part_number"]
		child_part_numbers = form.cleaned_data["child_part_numbers"]
		child_part_numbers_html=''
		for child_part_number in child_part_numbers:
			PnCpnMapping.objects.create(
				part_number_i=part_number,
				child_part_number_i=child_part_number,
				mapped_by=request.user,
			)
			child_part_numbers_html=child_part_numbers_html+f"<li>{child_part_number.name}</li>"
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The mapping of <b>{part_number.name}, {child_part_numbers_html}</b> for <b>{product_category.name}</b> is successful"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	

@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def pnprlps_mapping(request, current_product_category_id):
	form=PnPrlPsMappingForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		part_number = form.cleaned_data["part_number"]
		production_line = form.cleaned_data["production_line"]
		production_stations = form.cleaned_data["production_stations"]
		cycle_time = form.cleaned_data["cycle_time"]
		production_stations_html=''
		for production_station in production_stations:
			PnPrlPsMapping.objects.create(
				part_number_i=part_number,
				production_line_i=production_line,
				production_station_i=production_station,
				mapped_by=request.user,
			)
			production_stations_html=production_stations_html+f"<li>{production_station.name}</li>"

		pnprldata = PnPrlCtData.objects.filter(part_number_i=part_number, production_line_i=production_line)
		if pnprldata.exists():
			if pnprldata.cycle_time!=cycle_time:
				pnprldata=pnprldata.first()
				pnprldata.cycle_time=cycle_time
				pnprldata.edited_by=request.user
				pnprldata.save()
		else:
			PnPrlCtData.objects.create(
				part_number_i=part_number,
				production_line_i=production_line,
				cycle_time=cycle_time,
				edited_by=request.user,
			)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The mapping of <b>{part_number.name}, {production_line.name}, {production_stations_html}</b> for <b>{product_category.name} with the cycle time of {cycle_time}Secs </b> is successful"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)


@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def tps_mapping(request, current_product_category_id):
	form=TPsMappingForm(request.POST, request.FILES)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		tool_type = form.cleaned_data["tool_type"]
		tool = form.cleaned_data["tool"]
		production_line = form.cleaned_data["production_line"]
		production_station = form.cleaned_data["production_station"]
		full_life = form.cleaned_data["full_life"]
		low_life_consideration = form.cleaned_data["low_life_consideration"]
		tool_image = form.cleaned_data["tool_image"]
		temp_dic = {
			"tool_i" : tool,
			"production_station_i" : production_station,
			"full_life" : full_life,
			"low_life_consideration" : low_life_consideration,
			"tool_image" : tool_image,
			"mapped_by" : request.user
		}
		if tool_type == serve.Others.tool_fixtures:
			temp_dic["parts_freq"] = form.cleaned_data["parts_freq"]
		TPsMapping.objects.create(**temp_dic)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The mapping of <b>{tool.name}, {serve.get_pl_ps_display_format(production_station=production_station)}</b> for <b>{product_category.name}</b> is successful"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)


@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def pyps_mapping(request, current_product_category_id):
	form=PyPsMappingForm(request.POST)
	if form.is_valid():
		product_category = form.cleaned_data["product_category"]
		poka_yoke = form.cleaned_data["poka_yoke"]
		production_line = form.cleaned_data["production_line"]
		production_station = form.cleaned_data["production_station"]
		criticality_level = form.cleaned_data["criticality_level"]
		PyPsMapping.objects.create(
			poka_yoke_i = poka_yoke,
			production_station_i = production_station,
			criticality_level = criticality_level,
			mapped_by = request.user,
		)
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The mapping of <b>{poka_yoke.name}, {serve.get_pl_ps_display_format(production_station=production_station)}</b> for <b>{product_category.name}</b> is successful"))
		return redirect("dp_part", current_product_category_id=current_product_category_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_part", current_product_category_id=current_product_category_id)


@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.All_depts, serve.Designations.Assistant_Manager],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def oed_mapping(request, user_dept_id):
	form=OEEEventsForm(request.POST)
	if form.is_valid():
		oee_event = form.cleaned_data["oee_event"]
		oed_obj = OeDMapping.objects.filter(what_id = oee_event)
		if not oed_obj.exists():
			OeDMapping.objects.create(
				what_id = oee_event,
				dept_i_id = user_dept_id,
				mapped_user = request.user
			)
		else:
			oed_obj = oed_obj.first()
			if oed_obj.dept_i_id != user_dept_id:
				oed_obj.dept_i_id = user_dept_id
				oed_obj.mapped_user = request.user
				oed_obj.save()
			else:
				messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, mark_safe(f"The OEE event <b>{oee_event.name}</b> is alreay mapped to <b>{serve.get_icode_object(user_dept_id).name}</b>"))

		# Display the success message with mapped oee event and department
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The OEE event <b>{oee_event.name}</b> is successfully mapped to <b>{serve.get_icode_object(user_dept_id).name}</b>"))
		return redirect("dp_oee_event", current_dept_id=user_dept_id)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_oee_event", current_dept_id=user_dept_id)
	

@login_required(login_url="/accounts/login/")
def tech_data(request, technology_id):
	tech = serve.get_icode_object(technology_id)
	pls = serve.get_production_lines_of_tech(technology_id=technology_id)
	pns = serve.get_part_numbers_of_tech(technology_id=technology_id)
	context = {
		"parent": "Data Panel",
		"segment": "dp_part",
		"child": "Data Overview - Technology",
		"technology": tech,
		"production_lines": pls,
		"part_numbers": pns
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_tech_data.html", context)


@login_required(login_url="/accounts/login/")
def view_pns_of_ps(request, production_station_id):
	ps = serve.get_icode_object(production_station_id)
	pns = serve.get_part_numbers_of_ps(production_station_id=production_station_id)
	context = {
		"parent": "Data Panel",
		"segment": "dp_part",
		"child": "Part Numbers of Production Station",
		"production_station": ps,
		"part_numbers": pns
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_ps_pns.html", context)


@login_required(login_url="/accounts/login/")
def view_tools_of_ps(request, production_station_id):
	ps = serve.get_icode_object(production_station_id)
	tools = serve.get_tools_of_ps(production_station_id=production_station_id)
	context = {
		"parent": "Data Panel",
		"segment": "dp_part",
		"child": "Tools of Production Station",
		"production_station": ps,
		"tools": tools
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_ps_tools.html", context)


@login_required(login_url="/accounts/login/")
def view_pys_of_ps(request, production_station_id):
	ps = serve.get_icode_object(production_station_id)
	pokeyokes = serve.get_pys_of_ps(production_station_id=production_station_id)
	pyps_maps = PyPsMapping.objects.filter(poka_yoke_i__in=pokeyokes, production_station_i_id=production_station_id)

	context = {
		"parent": "Data Panel",
		"segment": "dp_part",
		"child": "Pokeyokes of Production Station",
		"production_station": ps,
		"pyps_maps": pyps_maps
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_pys_ps.html", context)


@login_required(login_url="/accounts/login/")
def view_pns_of_model(request, model_id):
	model = serve.get_icode_object(model_id)
	pns = serve.get_part_numbers_of_model(model_id=model_id)
	context = {
		"parent": "Data Panel",
		"segment": "dp_part",
		"child": f"Part Numbers of Model",
		"model": model,
		"part_numbers": pns
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_model_pns.html", context)


@login_required(login_url="/accounts/login/")
def view_pls_of_pn(request, part_number_id):
	part_number = serve.get_icode_object(part_number_id)
	pls = serve.get_production_lines_of_pn(part_number_id=part_number_id)
	context = {
		"parent": "Data Panel",
		"segment": "dp_part",
		"child": f"Production Lines of Part Number",
		"part_number": part_number,
		"production_lines": pls
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_pls_pn.html", context)


@login_required(login_url="/accounts/login/")
def tool_data(request, tool_id):
	tool = serve.get_icode_object(icode=tool_id)
	tool_type = serve.get_tool_type_by_tool(tool_id = tool_id)
	tps_map_data_list = []
	tps_maps = TPsMapping.objects.filter(tool_i=tool)  # get all mappings with this tool	
	for tps_map in tps_maps:
		tps_map_data_list.append((tps_map, ', '.join(serve.get_part_numbers_of_tps(tps_map=tps_map).values_list('name',flat=True))))	
	context = { 
		"parent" : "Data Panel",
		"segment" : "dp_part",
		"child" : f"Data - {tool_type.name}",
		"tool" : tool, 
		"tool_type" : tool_type,
		"tps_map_data_list" : tps_map_data_list,			
	}	
	return render(request, "pages/data_panel/dp_view_data_modify/dp_tool_data.html", context)


@login_required(login_url="/accounts/login/")
def poka_yoke_data(request, poka_yoke_id):
	poka_yoke = serve.get_icode_object(icode=poka_yoke_id)
	pyps_maps = PyPsMapping.objects.filter(poka_yoke_i=poka_yoke)  # get all mappings with this poka yoke	
	context = { 
		"parent" : "Data Panel",
		"segment" : "dp_part",	
		"child" : f"Data - Pokeyoke Name - {poka_yoke.name}",
		"poka_yoke" : poka_yoke, 
		"pyps_maps" : pyps_maps,			
	}	
	return render(request, "pages/data_panel/dp_view_data_modify/dp_py_data.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")

def delete_pyps_map(request, pyps_map_id):
	pyps_map = PyPsMapping.objects.get(id=pyps_map_id)
	poka_yoke_id = pyps_map.poka_yoke_i.icode
	pyps_map.delete()
	messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"deleted successfully"))
	return redirect('poka_yoke_data', poka_yoke_id=poka_yoke_id)  


@login_required(login_url="login")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def tps_life_param_edit(request, tps_map_id):
	tps_map = TPsMapping.objects.get(id = tps_map_id)
	tool_type = serve.get_tool_type_by_tool(tool_id = tps_map.tool_i_id)
	if request.POST:
		pre_tps_map = TPsMapping.objects.get(id = tps_map_id)
	form = ToolLifeParamEditForm(request.POST or None, instance = tps_map)
	if request.method == 'POST':
		if form.is_valid():
			full_life = form.cleaned_data['full_life']
			low_life_consideration = form.cleaned_data['low_life_consideration']
			parts_freq = form.cleaned_data['parts_freq']
			param_change_html = ""
			if pre_tps_map.full_life != full_life:
				param_change_html = f"<li>Tool life changed from {pre_tps_map.full_life} to {full_life}</li>"
			if pre_tps_map.low_life_consideration != low_life_consideration:
				param_change_html = param_change_html + f"<li>Tool\'s low life consideration changed from {pre_tps_map.low_life_consideration} to {low_life_consideration}</li>"
			if pre_tps_map.parts_freq != parts_freq:
				param_change_html = param_change_html + f"<li>Parts frequency changed from {pre_tps_map.parts_freq} to {parts_freq}</li>"
			form.save()										
			messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,
				mark_safe(
					f"<b>{serve.get_tool_type_by_tool(tool_id = tps_map.tool_i.icode).name}: { tps_map.tool_i.name}</b> \
					parameters modified successfully for the location <b>{serve.get_pl_ps_display_format(production_station=tps_map.production_station_i)}</b> {param_change_html}"
				)
			)
			return redirect("tool_data", tps_map.tool_i.icode)
		else:
			error_msg=""
			for field, errors in form.errors.as_data().items():
				error_msg= error_msg+";".join(errors[0].messages)
			messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
			return redirect("tps_life_param_edit", tps_map_id)
	context = {
		"parent" : "Data Panel",
		"segment" : "dp_part",
		"form": form,
		"tps_map": tps_map,
		"tool_type" : tool_type,
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_tps_life_param_edit.html", context)


@login_required(login_url="login")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def tps_part_numbers_map_edit(request, tps_map_id, edit_type):
	tps_map = TPsMapping.objects.get(id = tps_map_id)
	tool_type = serve.get_tool_type_by_tool(tool_id = tps_map.tool_i_id)
	part_numbers = Icodes.objects.filter(
		icode__in = TPsmapPnExMapping.objects.filter(tps_map_id=tps_map_id).values_list('part_number_i').distinct()
	).order_by("icode")	if edit_type==1 else serve.get_part_numbers_of_tps(tps_map=tps_map)
	if part_numbers.exists():
		form = ToolPartNumberMapEditForm(request.POST or None, pns = part_numbers)
	else:
		form = None
		messages.info(request, f"All partnumbers are already {'added' if edit_type else 'removed'}")
	if request.method == 'POST':
		if form.is_valid():	
			part_numbers = form.cleaned_data["part_numbers"]
			if edit_type==1:
				TPsmapPnExMapping.objects.filter(tps_map = tps_map, part_number_i__in = part_numbers).delete()
			else:
				for part_number in part_numbers:
					TPsmapPnExMapping.objects.create(tps_map = tps_map, part_number_i = part_number)
			part_numbers_html = ''
			for part_number in part_numbers:
				part_numbers_html=part_numbers_html+f"<li>{part_number.name}</li>"
			messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,
				mark_safe(f"""The partnumbers <b> {part_numbers_html} </b> is <b> {"added" if edit_type==1 else "<span style='color:#ff0000;font-weight:bold;'>removed</span>"}</b> for  <b> {tps_map.tool_i.name}, {tps_map.production_station_i.name}</b> successfully"""))	
			return redirect("tool_data", tps_map.tool_i.icode)	
	context = {
		"parent" : "Data Panel",
		"segment" : "dp_part",
		"form": form,
		"tps_map": tps_map,
		"tool_type" : tool_type,
		"edit_type": edit_type,
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_tps_pn_map_edit.html", context)


@login_required(login_url="login")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def tps_image_edit(request, tps_map_id):
	tps_map = TPsMapping.objects.get(id = tps_map_id)
	tool_type = serve.get_tool_type_by_tool(tool_id = tps_map.tool_i_id)
	form = ToolImageEditForm(request.POST,  request.FILES or None, instance = tps_map)	
	if request.method == 'POST':
		if form.is_valid():								
			form.save()										
			messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,
				mark_safe(
					f"<b>{serve.get_tool_type_by_tool(tool_id = tps_map.tool_i.icode).name}: { tps_map.tool_i.name}</b> \
					image modified successfully for the location <b>{serve.get_pl_ps_display_format(production_station=tps_map.production_station_i)}</b>"
				)
			)
			return redirect("tool_data", tps_map.tool_i.icode)
		else:
			error_msg=""
			for field, errors in form.errors.as_data().items():
				error_msg= error_msg+";".join(errors[0].messages)
			messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
			return redirect("tps_image_edit", tps_map_id)
	context = {
		"parent": "Data Panel",
		"segment": "dp_part",
		"form": form,
		"tps_map": tps_map,
		"tool_type" : tool_type,
	}
	return render(request, "pages/data_panel/dp_view_data_modify/dp_tps_image_edit.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_cs_selection_add(request, current_product_category_id):
	form=PlMPnSelectionForm(request.POST)
	if form.is_valid():
		production_line = form.cleaned_data["production_line"]
		part_number = form.cleaned_data["part_number"]
		return redirect("qa_patrol_cs_addition", production_line_id=production_line.icode, part_number_id=part_number.icode)
	else:
		error_msg=""
		for field, errors in form.errors.as_data().items():
			error_msg= error_msg+";".join(errors[0].messages)
		messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("dp_qa_patrol", current_product_category_id=serve.get_first_product_category().icode, current_checksheet_status_type_id=serve.get_checksheets_first_status_type().icode)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_cs_addition(request, production_line_id, part_number_id):
	pl = serve.get_icode_object(icode=production_line_id)
	pn = serve.get_icode_object(icode=part_number_id)
	qa_pcs_addition = None
	qa_pcs = PatrolCheckSheets.objects.filter(production_line_i = pl, part_number_i = pn, alive_flag = True)
	qa_pcss_of_pns = serve.get_qa_patrol_checksheets_of_pns(part_number_list = serve.get_part_numbers_of_pl(production_line_id = production_line_id), alive_flag = True)
	qa_pcss_of_pns_html_str = render_to_string('ajax_templates/drop_down_qa_pcs_for_duplication.html', {'options': qa_pcss_of_pns}) if qa_pcss_of_pns.exists() else ''
	if qa_pcs.exists():
		messages.add_message(request, messages.WARNING, mark_safe(f"Check sheet was already exist, <a href='{reverse('qa_patrol_cs_modification', args=(qa_pcs.first().id,))}'>click here to modify<a>"))
		qa_pcs_addition = False
	else:
		qa_pcs_addition = True
	context = {
		"parent" : "Data Panel",
		"segment" : "dp_qa_patrol",
		"child" : "QA Patrol Check Sheet - Addition",
		"production_line" : pl,
		"part_number" : pn,
		"qa_pcs_addition" : qa_pcs_addition,
		"qa_pcss_of_pns_html_str" : qa_pcss_of_pns_html_str,
		"operator_input_element_name" : serve.qa_pcs_operator_input_element_name,
		"inspection_input_element_name" :serve.qa_pcs_inspection_input_element_name,
		"operator_input_elements_max" :serve.qa_pcs_operator_input_elements_max,
		"inspection_input_elements_max" :serve.qa_pcs_inspection_input_elements_max,
		"inspection_input_element_max_len" :serve.qa_pcs_inspection_input_element_max_len,
		"operator_col_index" :serve.qa_pcs_extra_columns["operator_col"]["col_index"],
		"inspection_col_index" :serve.qa_pcs_extra_columns["inspection_col"]["col_index"],
	}
	return render(request, "pages/data_panel/dp_qa_patrol/dp_pcs_addition.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_cs_modification(request, qa_pcs_id):
	qa_pcs = PatrolCheckSheets.objects.get(id=qa_pcs_id)
	context = {
		"parent" : "Data Panel",
		"segment" : "dp_qa_patrol",
		"child" : "QA Patrol Check Sheet - Modification",
		"qa_pcs" : qa_pcs,
		"operator_input_element_name" :serve.qa_pcs_operator_input_element_name,
		"inspection_input_element_name" :serve.qa_pcs_inspection_input_element_name,
		"operator_input_elements_max" :serve.qa_pcs_operator_input_elements_max,
		"inspection_input_elements_max" :serve.qa_pcs_inspection_input_elements_max,
		"inspection_input_element_max_len" :serve.qa_pcs_inspection_input_element_max_len,
		"operator_col_index" :serve.qa_pcs_extra_columns["operator_col"]["col_index"],
		"inspection_col_index" :serve.qa_pcs_extra_columns["inspection_col"]["col_index"],
	}
	return render(request, "pages/data_panel/dp_qa_patrol/dp_pcs_modification.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def fetch_qa_patrol_cs_save(request, production_line_id, part_number_id):
	pl =serve.get_icode_object(icode=production_line_id)
	pn =serve.get_icode_object(icode=part_number_id)
	data = json.loads(request.body.decode('utf-8'))
	temp_str_list = []
	for line in data["checksheet_content"].splitlines():
		temp_str_list.append(line.strip())
	temp_str="".join(temp_str_list)
	qa_pcss = PatrolCheckSheets.objects.filter(production_line_i = pl, part_number_i = pn)
	if not qa_pcss.exists():
		qa_pcs = PatrolCheckSheets.objects.create(
			production_line_i = pl,
			part_number_i = pn,
			cs_version = 1,
			created_by = request.user,
			checksheet_html = temp_str,
    		alive_flag = True,
		)
		messages.add_message(request, messages.SUCCESS, mark_safe(f"New check sheet add successfully, <a href='{reverse('qa_patrol_cs_view', args=(qa_pcs.id,))}'>click here to view<a>"))
		return render(request, 'msg_templates/messages.html')
	else:
		for qa_pcs in qa_pcss.filter(alive_flag = True,):
			qa_pcs.alive_flag = False
			qa_pcs.save()
		qa_pcs = PatrolCheckSheets.objects.create(
			production_line_i = pl,
			part_number_i = pn,
			cs_version = qa_pcss.count()+1,
			created_by = request.user,
			checksheet_html = temp_str,
    		alive_flag = True,
		)
		messages.add_message(request, messages.SUCCESS, mark_safe(f"Check sheet modified successfully, <a href='{reverse('qa_patrol_cs_view', args=(qa_pcs.id,))}'>click here to view<a>"))
		return render(request, 'msg_templates/messages.html')


@login_required(login_url="/accounts/login/")
def qa_patrol_cs_view(request, qa_pcs_id):
	qa_pcs = PatrolCheckSheets.objects.get(id=qa_pcs_id)
	context = {
		"parent" : "Data Panel",
		"segment" : "dp_qa_patrol",
		"child" : "QA Patrol Check Sheet - View",
		"qa_pcs" : qa_pcs,
	}
	return render(request, "pages/data_panel/dp_qa_patrol/dp_pcs_view.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.Craftsman],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_patrol_cs_deactivate(request, qa_pcs_id):
	qa_pcs = PatrolCheckSheets.objects.get(id=qa_pcs_id)
	if request.method == "POST":
		qa_pcs.alive_flag = False
		qa_pcs.deactivated_by = request.user
		qa_pcs.save()
		messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"Checksheet deactivated successfully, <b>{qa_pcs.production_line_i.name}-{qa_pcs.part_number_i.name} - V{qa_pcs.cs_version}</b>"))
		return redirect("dp_qa_patrol", current_product_category_id=serve.get_first_product_category().icode, current_checksheet_status_type_id=serve.get_checksheets_first_status_type().icode)
	context = {
		"parent" : "Data Panel",
		"segment" : "dp_qa_patrol",
		"child" : "QA Patrol Check Sheet - Deactivate",
		"qa_pcs" : qa_pcs,
	}
	return render(request, "pages/data_panel/dp_qa_patrol/dp_pcs_deactivate.html", context)


@login_required(login_url="/accounts/login/")
def dp_pn_drawings(request, current_product_category_id, current_part_drawing_status_id, current_pagination_option_id, current_page_num):
	all_part_numbers = serve.get_part_numbers(product_category_id=current_product_category_id)
	part_numbers_with_drawing = serve.get_icode_objects(list(PnDrawings.objects.values_list('part_number_i', flat=True).distinct()))
	if current_part_drawing_status_id == serve.Others.partnumbers_with_drawings.icode:
		part_numbers = [x for x in all_part_numbers if x in part_numbers_with_drawing]
	elif current_part_drawing_status_id == serve.Others.Partnumbers_without_drawings.icode:
		part_numbers = all_part_numbers.exclude(icode__in=part_numbers_with_drawing)
	else:
		part_numbers = all_part_numbers
	current_pagination_option =  serve.get_icode_object(current_pagination_option_id)
	context = {
        "parent" : "Data Panel",
        "segment": "Partnumber Drawings",
        "child": "Partnumber Drawings",
		"part_drawing_status": serve.get_pn_drawing_status_options,
		"current_product_category" : serve.get_icode_object(current_product_category_id),
		"current_part_drawing_status" :  serve.get_icode_object(current_part_drawing_status_id),
		"product_categories" : serve.get_product_categories(),
		"pagination_options": serve.get_pagination_options(),
		"current_pagination_option":current_pagination_option,
		"current_page_num": current_page_num,
		"part_numbers_pagination": paginator.Paginator(part_numbers, current_pagination_option.description).get_page(current_page_num),
    }
	return render(request, 'pages/data_panel/dp_pn_drawings/dp_pn_drawings.html', context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Engg, serve.Designations.Assistant_Manager],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def add_pn_drawings(request, part_number_id):
	if request.method == 'POST':
		form=PnDrawingForm(request.POST, request.FILES)	
		if form.is_valid():
			latest_version_of_drawings = (
                PnDrawings.objects.filter(part_number_i=serve.get_icode_object(part_number_id))
                .order_by('-version')
                .values_list('version', flat=True)
                .first()
            )
			version = 1 if latest_version_of_drawings is None else latest_version_of_drawings + 1                            
			drawing_file = form.cleaned_data["drawing_file"]
			change_desc = form.cleaned_data["change_desc"]
			PnDrawings.objects.create(
                part_number_i = serve.get_icode_object(part_number_id),
                drawing_file = drawing_file,
                version = version,
                added_user = request.user,
				change_desc = change_desc
            )
			messages.add_message(request,custom_messages.SUCCESS_MODAL_MESSAGE,
				mark_safe(
					f"Drawing added for this partnumber (<b>{serve.get_icode_object(part_number_id).name}</b>) successfully! "					
				)
			)
			return redirect('view_pn_drawings', part_number_id=part_number_id)
	else:
		form=PnDrawingForm()
	context = {
		"parent" : "Data Panel",
        "segment": "Partnumber Drawings",
		"child": "Add Part Drawing",
		"form": form,
		"part_number_id": part_number_id
	}
	return render(request, 'pages/data_panel/dp_pn_drawings/dp_add_pn_drawings.html',context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Engg, serve.Designations.Assistant_Manager],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def update_pn_drawings(request, part_number_id):
	if request.method == 'POST':
		form=PnDrawingForm(request.POST, request.FILES)	
		if form.is_valid():
			latest_version_of_drawings = (
				PnDrawings.objects.filter(part_number_i=serve.get_icode_object(part_number_id))
				.order_by('-version')
				.values_list('version', flat=True)
				.first()
			)
			version = 1 if latest_version_of_drawings is None else latest_version_of_drawings + 1                            
			drawing_file = form.cleaned_data["drawing_file"]
			change_desc = form.cleaned_data["change_desc"]
			PnDrawings.objects.create(
				part_number_i = serve.get_icode_object(part_number_id),
				drawing_file = drawing_file,
				version = version,
				added_user = request.user,
				change_desc = change_desc
			)
			messages.add_message(request,custom_messages.SUCCESS_MODAL_MESSAGE,
				mark_safe(
					f"Drawing updated for this partnumber (<b>{serve.get_icode_object(part_number_id).name}</b>) successfully! "					
				)
			)
			return redirect('view_pn_drawings', part_number_id=part_number_id)
	else:
		form=PnDrawingForm()
	drawings_obj = (PnDrawings.objects.filter(part_number_i=serve.get_icode_object(part_number_id)).order_by('-version') )
	context = {
		"parent" : "Data Panel",
        "segment": "Partnumber Drawings",
		"child": "Update Part Drawing",
		"form": form,
		"drawings_obj": drawings_obj,
		"part_number_id": part_number_id
	}
	return render(request, 'pages/data_panel/dp_pn_drawings/dp_update_pn_drawings.html',context)


@login_required(login_url="login")
def view_pn_drawings(request, part_number_id):
    drawings_obj = (PnDrawings.objects.filter(part_number_i=serve.get_icode_object(part_number_id)).order_by('-version') )
    context = {
        "parent" : "Data Panel",
        "segment": "Partnumber Drawings",
        "child": "Partnumber Drawing",
        "drawings_obj": drawings_obj,
		"part_number_id" : part_number_id
    }
    return render(request, 'pages/data_panel/dp_pn_drawings/dp_view_pn_drawings.html', context)


@login_required(login_url="login")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Development_team, serve.Designations.All_designations]), redirect_url="user_access_denied")
def wf_form_addition(request):
	current_workflow_status_type = serve.Others.active_workflows_option 
	context = {
        "parent": "Data Panel",
        "segment": "Workflows",
		"child" : "Workflow - Form Creation Page",
		"root": [
            {"name": "xylem_workflows", "url":  reverse( "dp_workflows",kwargs={"current_workflow_status_type_id": current_workflow_status_type.icode})},
            {"name": "form Creation", "url": reverse("wf_form_addition")},
        ],
		"depts":serve.get_depts(),
    }	
	return render(request, "pages/data_panel/dp_workflows/dp_wf_form_addition.html", context)


@login_required(login_url="/accounts/login/")
def dp_wf_form_save(request):
	data = json.loads(request.body.decode("utf-8"))
	form_name = data.get("form_name", "").strip()
	sections = data.get("sections")
	approvers = data.get("approvers")
	mapping = data.get("mapping")
	wf_form_id = data.get("wf_form_id")
	existing_form = WorkflowForms.objects.filter(form_name__iexact=form_name,status_flag=1).first()
	if existing_form:
		return JsonResponse({"status": "exists","message": f"Form '{form_name}' already exists."})
	if wf_form_id:
		wf_fms_qs = WorkflowForms.objects.filter(id=wf_form_id, status_flag=1)
		if wf_fms_qs.exists():
			for wf_fs in wf_fms_qs:
				wf_fs.status_flag = 0
				wf_fs.save()
			existing_form = wf_fms_qs.first()
			new_version = existing_form.fs_version + 1
			wf_form = WorkflowForms.objects.create(
				form_name=form_name,
				dept_i=existing_form.dept_i,
				fs_version=new_version,
				status_flag=1,
				created_by=request.user,
			)
			messages.add_message(request, messages.SUCCESS,mark_safe(f" WorkflowForm <b>{form_name}</b> updated successfully as "f"<b>V{new_version}</b>"))
			return render(request, 'msg_templates/messages.html')
	# Create new form
	wf_form = WorkflowForms.objects.create(form_name=form_name,fs_version=1,status_flag=1,created_by=request.user)
	# save sections
	form_section_objs = {}
	for key, section_data in sections.items():
		section_order = int(key.split("_")[-1])
		section_obj = WorkflowFormSections.objects.create(
			form_name=wf_form,
			section_name=section_data.get("name"),
			section_order=section_order,
			section_html=section_data.get("html"),
		)
		form_section_objs[section_order] = section_obj
		dept_icodes = section_data.get("department")
		if dept_icodes: 
			mapping_depts = Icodes.objects.filter(icode__in=dept_icodes)
			for assigned_dept in mapping_depts:
				workflowSectionDepartmentMapping.objects.create(section=section_obj,assigned_department=assigned_dept)
	# SAVE APPROVERS 
	approver_section_objs = {}
	for key, section_data in approvers.items():
		approver_order = int(key.split("_")[-1])
		approver_section_objs[approver_order] = []
		alert_data = section_data.get("alert",{}) 
		auto_approve = section_data.get("autoApprove")
		auto_approve_days = section_data.get("autoApproveDays") 
		for dept_apr in section_data.get("dept_based_users",[]):
			dept_bsd_usr = Icodes.objects.filter(icode=dept_apr.get("dept_appr_dept")).first()
			for user_data in dept_apr.get("users"):
				user_department = Icodes.objects.filter(icode=user_data.get("user_department")).first() if user_data.get("user_department") else None
				user = UserProfile.objects.filter(id=user_data.get("user")).first()
				if not user:
					continue
				# Save row for department-based approver
				approver_obj = WorkflowFormApprover.objects.create(
					approver_order=approver_order,
					form=wf_form,
					dept_based_user=dept_bsd_usr,
					user_dept=user_department,
					user=user,
					auto_approve=auto_approve,
					auto_approve_days=auto_approve_days,
					alert_name=alert_data.get("alert_name"),
					daywise=alert_data.get("daywise"),
					weekly_day=alert_data.get("weeklyDay"),
					monthly_day=alert_data.get("monthlyDay"),
					time=alert_data.get("time"),
				)
				approver_section_objs[approver_order].append(approver_obj)
		for approver in section_data.get("static_approvers", []):
			user_id = approver.get("user")
			user_department = Icodes.objects.filter(icode=approver.get("user_department")).first()
			user = UserProfile.objects.filter(id=user_id).first()
			if not user:
				continue
			approver_obj = WorkflowFormApprover.objects.create(
				approver_order=approver_order,
				form=wf_form,
				user_dept=user_department,
				user=user,
				auto_approve=auto_approve,
				auto_approve_days=auto_approve_days,
				alert_name=alert_data.get("alert_name"),
				daywise=alert_data.get("daywise"),
				weekly_day=alert_data.get("weeklyDay"),
				monthly_day=alert_data.get("monthlyDay"),
				time=alert_data.get("time"),
			)
			approver_section_objs[approver_order].append(approver_obj)

	# SAVE MAPPING
	for map_item in mapping:
		form_section_num = int(map_item.get("form_section"))
		approver_section_str = map_item.get("approver_section", "approver_0")
		approver_section_num = int(approver_section_str.split("_")[-1])
		parallel_order = int(map_item.get("parallel_order", 1))
		stage = int(map_item.get("stage", 1))
		form_section_obj = form_section_objs.get(form_section_num)
		approver_objs = approver_section_objs.get(approver_section_num, [])
		for idx, approver_obj in enumerate(approver_objs, start=1):
			WorkflowApproverMapping.objects.create(
				form_section=form_section_obj,
				approver_section=approver_obj,
				approver_level=stage,   
				parallel_order=parallel_order,  
			)
	messages.add_message(request, messages.SUCCESS,mark_safe(f" WorkflowForm <b>{form_name}</b> saved successfully as "f"<b>V{wf_form.fs_version}</b>"),)
	return render(request, 'msg_templates/messages.html')


# Ajax for dependent forms
@login_required(login_url="login")
def ajax_load_all_users(request):
	users = serve.get_all_users()
	return render(request, 'ajax_templates/drop_down_users.html', {'user_options': users})


@login_required(login_url="login")
def ajax_load_operators(request):
	users = serve.get_all_operators()
	return render(request, 'ajax_templates/drop_down_users.html', {'user_options': users})


@login_required(login_url="login")
def ajax_load_empty_option(request):
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': []})


@login_required(login_url="login")
def ajax_load_product_technologies(request):
	product_category_id = request.GET.get('product_category_id')
	product_technologies = serve.get_product_technologies(product_category_id=product_category_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': product_technologies})


@login_required(login_url="login")
def ajax_load_product_models(request):
	product_category_id = request.GET.get('product_category_id')
	product_models = serve.get_product_models(product_category_id=product_category_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': product_models})


@login_required(login_url="login")
def ajax_load_product_models_of_pl(request):
	production_line_id = request.GET.get('production_line_id')
	product_models=serve.get_product_models_of_pl(production_line_id=production_line_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': product_models})


@login_required(login_url="login")
def ajax_load_product_models_of_ps(request):
	production_station_id = request.GET.get('production_station_id')
	product_models=serve.get_product_models_of_ps(production_station_id=production_station_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': product_models})


@login_required(login_url="login")
def ajax_load_product_models_of_pls(request):
	production_line_id_list_str = request.GET.get('production_line_id_list_str')
	product_models=serve.get_product_models_of_pls(production_line_id_list=production_line_id_list_str.split(","))
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': product_models})


@login_required(login_url="login")
def ajax_load_product_models_of_pl_qa_pcs(request):
	production_line_id = request.GET.get('production_line_id')
	product_models_pl_qa_pcs = serve.get_product_models_of_pl_qa_pcs(production_line_id=production_line_id, alive_flag=True)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': product_models_pl_qa_pcs})


@login_required(login_url="login")
def ajax_load_production_lines(request):
	product_category_id = request.GET.get('product_category_id')
	production_lines = serve.get_production_lines(product_category_id=product_category_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': production_lines})


@login_required(login_url="login")
def ajax_load_production_lines_of_pn(request):
	part_number_id = request.GET.get('part_number_id')
	production_lines = serve.get_production_lines_of_pn(part_number_id=part_number_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': production_lines})


@login_required(login_url="login")
def ajax_load_production_lines_of_qa_pcss(request):
	product_category_id = request.GET.get('product_category_id')
	production_lines = serve.get_production_lines_of_qa_pcss(product_category_id=product_category_id, alive_flag=True)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': production_lines})


@login_required(login_url="login")
def ajax_load_department_of_wfs(request):
	departments = serve.get_depts()	
	return render(request, 'ajax_templates/drop_down_departments.html', {'departments': departments})


@login_required(login_url="login")
def ajax_load_dept_users_of_wfs(request):
	dept_code = request.GET.get("dept_id")
	users = UserProfile.objects.filter(dept_i__icode=dept_code,is_active=True,)
	return render(request, 'ajax_templates/drop_down_users.html', {'user_options': users})


@login_required(login_url="login")
def ajax_load_production_lines_of_tools(request):
	product_category_id = request.GET.get('product_category_id')
	tool_type_id = request.GET.get('tool_type_id')
	production_lines = serve.get_production_lines_of_tools(product_category_id=product_category_id, tool_type_id=tool_type_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': production_lines})


@login_required(login_url="login")
def ajax_load_production_stations(request):
	production_line_id = request.GET.get('production_line_id')
	production_stations = serve.get_production_stations(production_line_id=production_line_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': production_stations})


@login_required(login_url="login")
def ajax_load_production_stations_of_pl_tools(request):
	production_line_id = request.GET.get('production_line_id')
	tool_type_id = request.GET.get('tool_type_id')
	production_stations = serve.get_production_stations_of_pl_tools(production_line_id=production_line_id, tool_type_id=tool_type_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': production_stations})


@login_required(login_url="login")
def ajax_load_part_numbers(request):
	product_category_id = request.GET.get('product_category_id')
	part_numbers = serve.get_part_numbers(product_category_id=product_category_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': part_numbers})


@login_required(login_url="login")
def ajax_load_part_numbers_of_ps(request):
    production_station_id = request.GET.get('production_station_id')
    part_numbers_ps = serve.get_part_numbers_of_ps(production_station_id=production_station_id)
    return render(request, 'ajax_templates/drop_down_icodes.html', {'options': part_numbers_ps})

@login_required(login_url="login")
def ajax_load_part_number_map_data(request):
	part_number_id = request.GET.get('part_number_id')
	part_number=Icodes.objects.get(icode=part_number_id)
	pnmt_map=PnMTMapping.objects.filter(part_number_i=part_number).first()
	pncpn_map=PnCpnMapping.objects.filter(part_number_i=part_number)
	pnprlps_map=PnPrlPsMapping.objects.filter(part_number_i=part_number)
	pnprpls_map_dic={}
	for production_line_i in pnprlps_map.values_list("production_line_i", flat=True).distinct():
		station_list=[]
		for station_i in pnprlps_map.filter(production_line_i=production_line_i).values_list("production_station_i", flat=True):
			station_list.append(Icodes.objects.get(icode=station_i).name)
		pnprpls_map_dic[Icodes.objects.get(icode=production_line_i).name]={
			"ct":serve.get_ct_of_pn_on_pl(part_number=part_number, production_line_id=production_line_i),
			"stations":station_list
		}
	part_data={
		"part_number":part_number,
		"pnmt_map" : pnmt_map,
		"pncpn_map" : pncpn_map,
		"pnprpls_map_dic" : pnprpls_map_dic,
	}
	return render(request, 'ajax_templates/part_data.html', part_data)


@login_required(login_url="login")
def ajax_load_part_numbers_of_ps(request):
	production_station_id = request.GET.get('production_station_id')
	part_numbers_ps = serve.get_part_numbers_of_ps(production_station_id=production_station_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': part_numbers_ps})


@login_required(login_url="login")
def ajax_load_part_numbers_of_pl_m(request):
	production_line_id = request.GET.get('production_line_id')
	part_numbers_pl = serve.get_part_numbers_of_pl(production_line_id=production_line_id)
	model_id = request.GET.get('model_id')
	part_numbers_m = serve.get_part_numbers_of_model(model_id=model_id)
	part_numbers = Icodes.objects.filter(Q(icode__in=part_numbers_pl) & Q(icode__in=part_numbers_m)).order_by("icode")
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': part_numbers})


@login_required(login_url="login")
def ajax_load_part_numbers_of_ps_m(request):
    production_station_id = request.GET.get('production_station_id')
    part_numbers_ps = serve.get_part_numbers_of_ps(production_station_id=production_station_id)
    model_id = request.GET.get('model_id')
    part_numbers_m = serve.get_part_numbers_of_model(model_id=model_id)
    part_numbers = Icodes.objects.filter(Q(icode__in=part_numbers_ps) & Q(icode__in=part_numbers_m)).order_by("icode")
    return render(request, 'ajax_templates/drop_down_icodes.html', {'options': part_numbers})


@login_required(login_url="login")
def ajax_load_part_numbers_of_pls_ms(request):
	production_line_id_list_str = request.GET.get('production_line_id_list_str')
	part_numbers_pls = serve.get_part_numbers_of_pls(production_line_id_list=production_line_id_list_str.split(","))
	model_id_list_str = request.GET.get('model_id_list_str')
	part_numbers_ms = serve.get_part_numbers_of_models(model_id_list=model_id_list_str.split(","))
	part_numbers = Icodes.objects.filter(Q(icode__in=part_numbers_pls) & Q(icode__in=part_numbers_ms)).order_by("icode")
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': part_numbers})


@login_required(login_url="login")
def ajax_load_part_numbers_of_pl_m_qa_pcs(request):
	production_line_id = request.GET.get('production_line_id')
	part_numbers_pl_qa_pcs = serve.get_part_numbers_of_pl_qa_pcs(production_line_id=production_line_id, alive_flag=True)
	model_id = request.GET.get('model_id')
	part_numbers_m = serve.get_part_numbers_of_model(model_id=model_id)
	part_numbers = Icodes.objects.filter(Q(icode__in=part_numbers_pl_qa_pcs) & Q(icode__in=part_numbers_m)).order_by("icode")
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': part_numbers})


@login_required(login_url="login")
def ajax_load_part_numbers_of_tps(request):
	tps_map_id = request.GET.get('tps_map_id')
	production_stations = serve.get_part_numbers_of_tps(tps_map_id=tps_map_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': production_stations})


@login_required(login_url="login")
def ajax_load_child_part_numbers(request):
	product_category_id = request.GET.get('product_category_id')
	child_part_numbers = serve.get_child_part_numbers(product_category_id=product_category_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': child_part_numbers})


@login_required(login_url="login")
def ajax_load_child_part_numbers_of_pn(request):
	part_number_id = request.GET.get('part_number_id')
	child_part_numbers = serve.get_child_part_numbers_of_pn(part_number_id=part_number_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': child_part_numbers})


@login_required(login_url="login")
def ajax_load_child_part_numbers_of_pns(request):
	part_number_id_list_str = request.GET.get('part_number_id_list_str')
	child_part_numbers = serve.get_child_part_numbers_of_pns(part_number_id_list=part_number_id_list_str.split(","))
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': child_part_numbers})


@login_required(login_url="login")
def ajax_load_qa_pcss_of_production_line(request):
	production_line_id = request.GET.get('production_line_id')
	qa_pcss = serve.get_qa_patrol_checksheets_of_pl(production_line_id = production_line_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': qa_pcss})


@login_required(login_url="login")
def ajax_load_product_rejection_reasons(request):
	product_category_id = request.GET.get('product_category_id')
	rejection_reasons = serve.get_rejection_reasons(product_category_id=product_category_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': rejection_reasons})


@login_required(login_url="login")
def ajax_load_tools(request):
	product_category_id = request.GET.get('product_category_id')
	tool_type_id = request.GET.get('tool_type_id')
	tools = serve.get_tools(product_category_id=product_category_id, tool_type_id=tool_type_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': tools})


@login_required(login_url="login")
def ajax_load_tools_of_ps(request):
	production_station_id = request.GET.get('production_station_id')
	tool_type_id = request.GET.get('tool_type_id')
	tools = serve.get_tools_of_ps(production_station_id=production_station_id, tool_type_id=tool_type_id)	
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': tools})


@login_required(login_url="login")
def ajax_load_poka_yokes(request):
	product_category_id = request.GET.get('product_category_id')
	poka_yokes = serve.get_poka_yokes(product_category_id=product_category_id)
	return render(request, 'ajax_templates/drop_down_icodes.html', {'options': poka_yokes})


@login_required(login_url="login")
def fetch_qa_pcs_addition_upload(request):
	uploaded_file = request.FILES.get("fileInput")
	if "customRadio" in request.POST and request.POST.get("customRadio"):
		return render(request, 'fetch_templates/qa_pcs_table.html', {"table_data": mark_safe(PatrolCheckSheets.objects.get(id=int(request.POST.get("qa_pcs_select"))).checksheet_html)})
	if uploaded_file is not None:
		df = pd.read_excel(uploaded_file)

		# Handle merged cells by filling NaN to duplicate their values
		df = df.ffill()
		target_columns = [
			"STATION WORK",
			"INSPECTION ITEMS",
			"SPECIFICATION",
			"INSPECTION METHOD",
		]
		
		# Convert column names to lowercase and select only specific columns
		def case_insensitive_match(col):
			return next((c for c in df.columns if str(c).lower() == col.lower()), None)

		selected_columns = [case_insensitive_match(col) for col in target_columns]

		if all(selected_columns):
			df_selected = df[selected_columns]
			# Inserting "OPERATOR NAME" and "RESULT" columns
			for i in serve.qa_pcs_extra_columns:
				df_selected.insert(serve.qa_pcs_extra_columns[i]['col_index'], serve.qa_pcs_extra_columns[i]['name'], ['' for i in df_selected["STATION WORK"]])

			# df_selected = df_selected.dropna(how="all")
			table_html = df_selected.to_html(index=False, na_rep="", classes="table table-striped")
			table_html = table_html.replace('border="1"', '') 
			table_html = table_html.replace('style="text-align: right;"', '')  
			return render(request, 'fetch_templates/qa_pcs_table.html', {"table_data":mark_safe(table_html)})
		else:
			messages.add_message(request, custom_messages.DANGER_DISMISSABLE, "Unable to get the columns, Kindly load excel file as per requirement")
			return render(request, 'msg_templates/messages.html')

