from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models import Max, Q, F
import datetime,logging
from django.core import paginator

import xylem.custom_messages.constants as custom_messages
from xylem.settings import XYLEM_MODE, XYLEM_MODE_DIC
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom, view_eligibity_test
from xylem_apps.a000_xylem_master import serve 
from xylem_apps.a000_xylem_master.models import Icodes

from .forms import FourMForm
from .models import FourMFormModel, FourMMapping, FourMApprovals
from .models import approval_response_min_len, approval_response_max_len

a006_logger = logging.getLogger(serve.an_4m_digitalization)

# Create your views here.
@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.All_depts, serve.Designations.All_designations],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def four_m_form(request):
	form=FourMForm(request.POST or None)
	form.user(request.user)
	if request.method == "POST":
		if form.is_valid():
			four_m_point = form.cleaned_data["four_m_point"]
			change_from = form.cleaned_data["change_from"]
			before_desc = form.cleaned_data["before_desc"]
			after_desc = form.cleaned_data["after_desc"]
			change_desc = form.cleaned_data["change_desc"]
			supplier_rel_chng = form.cleaned_data["supplier_rel_chng"]==serve.Others.yes_option
			approval_depts = form.cleaned_data["approval_depts"]
			fm = FourMFormModel.objects.create(
				four_m_point_i = four_m_point,
				fm_change_datetime = change_from,
				fm_before_desc = before_desc,
				fm_after_desc = after_desc,
				fm_change_desc = change_desc,
				supplier_rel_chng = supplier_rel_chng,
				raised_user= request.user
			)
			production_lines = form.cleaned_data["production_lines"]
			models = form.cleaned_data["models"]
			part_numbers = form.cleaned_data["part_numbers"]
			child_part_numbers = form.cleaned_data["child_part_numbers"]
			map_list = []
			for i in production_lines:
				map_list.append(FourMMapping(four_m_form_ref=fm, mapped_i=i))
			for i in models:
				map_list.append(FourMMapping(four_m_form_ref=fm, mapped_i=i))
			for i in part_numbers:
				map_list.append(FourMMapping(four_m_form_ref=fm, mapped_i=i))
			if supplier_rel_chng:
				for i in child_part_numbers:
					map_list.append(FourMMapping(four_m_form_ref=fm, mapped_i=i))
			FourMMapping.objects.bulk_create(map_list)
			map_list=[]
			map_list.append(FourMApprovals(four_m_form_ref=fm, approval_needed_dept_i=serve.Depts.Inprocess_QA))
			map_list.append(FourMApprovals(four_m_form_ref=fm, approval_needed_dept_i=serve.Depts.MFG))

			if not(request.user.dept_i==serve.Depts.Inprocess_QA or request.user.dept_i==serve.Depts.Inprocess_QA):
				map_list.append(FourMApprovals(four_m_form_ref=fm, approval_needed_dept_i=request.user.dept_i))
				
			for i in approval_depts:
				map_list.append(FourMApprovals(four_m_form_ref=fm, approval_needed_dept_i=i))
			FourMApprovals.objects.bulk_create(map_list)
			try:
				serve.get_from_background_worker_api(serve.a006_get_four_m_mail_url + str(fm.id), timeout=5)								
				a006_logger.info(f"4M Change approval request triggred successfully for Form ID: {fm.id}")
			except Exception:				 
				a006_logger.warning(f"Unable to trigger 4M Change approval request for Form ID: {fm.id}", exc_info=True)
			messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,
				mark_safe(f"4M form data submitted successfully. <a href='{reverse('a006:four_m_report_view', args=(fm.id,))}'><u> Ref ID: {'-'.join([serve.xylem_code,serve.an_4m_digitalization,str(fm.id)])} </u></a>")
			)
		else:
			error_msg = ""
			for field, errors in form.errors.as_data().items():
				error_msg = error_msg+";".join(errors[0].messages)
			messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
		return redirect("a006:four_m_form")
	context = {
		"parent" : "Entry Forms",
		"segment" : "4M Entry Form",
		"form" : form
	}
	return render(request,"a006/four_m_form.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.All_depts, serve.Apps.A0064MDigitalization.min_approver_designation],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def four_m_approval(request,current_pagination_option_id, current_page_num):
	current_pagination_option = serve.get_icode_object(current_pagination_option_id)
	new_four_m_forms = FourMFormModel.objects.filter(a006_fma_fr__approval_needed_dept_i=request.user.dept_i, a006_fma_fr__response=None, fm_status= None)
	context = {
        "parent" : "Approval",
		"segment" : "New 4M Forms",
		"app_name" : serve.an_4m_digitalization,
		"pagination_options": serve.get_pagination_options(),
		"current_pagination_option": current_pagination_option,
		"new_four_m_forms_pagination": paginator.Paginator(new_four_m_forms.order_by('id'), current_pagination_option.description).get_page(current_page_num),			       
    }
	return render(request, 'a006/four_m_approval.html', context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.All_depts, serve.Apps.A0064MDigitalization.min_approver_designation],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def four_m_approval_view(request, four_m_form_id,current_pagination_option_id, current_page_num):
	four_m_form = FourMFormModel.objects.get(id=four_m_form_id)
	if request.method == "POST":
		response = request.POST.get("approver_response")
		response_desc = request.POST.get("response_desc")
		appr_elem = FourMApprovals.objects.filter(four_m_form_ref=four_m_form, approval_needed_dept_i=request.user.dept_i, response = None).first()
		if appr_elem.response is None: 
			if response == '1':
				appr_elem.response = True
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,
                                     mark_safe(f"4M Form <a>{'-'.join([serve.xylem_code,serve.an_4m_digitalization,str(four_m_form.id)])} </a> is <b>approved</b> successfully"))
			else:
				appr_elem.response = False
				messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE,
                                     mark_safe(f"4M Form <a>{'-'.join([serve.xylem_code,serve.an_4m_digitalization,str(four_m_form.id)])} </a> is <span style='color:#ff0000;font-weight:bold;'>rejected</span> successfully"))
				four_m_form.fm_status = False
				four_m_form.save()
			appr_elem.response_desc = response_desc
			appr_elem.responded_user = request.user
			appr_elem.response_datetime = timezone.now()
			appr_elem.approval_mode = serve.ApprovalModes.xylem_local_site
			appr_elem.save()
			if all(FourMApprovals.objects.filter(four_m_form_ref = four_m_form).values_list('response', flat=True)):
				four_m_form.fm_status = True
				four_m_form.save()
		return redirect("a006:four_m_approval", current_pagination_option_id = current_pagination_option_id, current_page_num = current_page_num)	
	approval_list = FourMApprovals.objects.filter(four_m_form_ref = four_m_form, approval_needed_dept_i = request.user.dept_i)
	if approval_list.exists():
		appr_elem = approval_list.first()
		if appr_elem.response is None:
			mapped_items = FourMMapping.objects.filter(four_m_form_ref=four_m_form)	
			product_category_id = (mapped_items.first().mapped_i.icode//serve.IcodeSplitup.product_category["period"])*serve.IcodeSplitup.product_category["period"]
			mapped_items = list(mapped_items.values_list("mapped_i", flat=True))
			product_models = Icodes.objects.filter(
				Q(icode__in=mapped_items) & 
				Q(icode__in=serve.get_product_models(product_category_id=product_category_id))
			).order_by("icode")
			production_lines = Icodes.objects.filter(
				Q(icode__in=mapped_items) & 
				Q(icode__in=serve.get_production_lines(product_category_id=product_category_id))
			).order_by("icode")
			part_numbers = Icodes.objects.filter(
				Q(icode__in=mapped_items) & 
				Q(icode__in=serve.get_part_numbers(product_category_id=product_category_id))
			).order_by("icode")
			child_part_numbers = {}
			if four_m_form.supplier_rel_chng:
				child_part_numbers = Icodes.objects.filter(
					Q(icode__in=mapped_items) & 
					Q(icode__in=serve.get_child_part_numbers(product_category_id=product_category_id))
				).order_by("icode")
			approval_list_depts = []
			for i in FourMApprovals.objects.filter(four_m_form_ref = four_m_form):
				if i.response is None:
					response = serve.st_pend_str
					responded_user = serve.na_str
					response_datetime = serve.na_str
					response_desc = i.response_desc
				else:
					response =  serve.st_appr_str if i.response else serve.st_rej_str
					response_datetime = i.response_datetime
					responded_user = serve.get_user_display_format(user=i.responded_user)
					response_desc = i.response_desc
				approval_list_depts.append([i.approval_needed_dept_i.name, responded_user, response, response_datetime, response_desc])
			
			if four_m_form.fm_status is None:
				overall_status = serve.st_pend_str
			else:
				overall_status = serve.st_appr_str if four_m_form.fm_status else serve.st_rej_str						
			context = {
				"parent" : "Approval",
				"segment" : "New 4M Forms",     
				"child" : "New 4M Forms - Approval View",
				"approval_response_min_len" : approval_response_min_len,
				"approval_response_max_len" : approval_response_max_len,
				"four_m_form" : four_m_form,
				"xylem_code" : serve.xylem_code, 
				"app_name" : serve.an_4m_digitalization,       
				"production_lines" : production_lines,
				"product_models" : product_models,
				"part_numbers" : part_numbers,    
				"child_part_numbers" : child_part_numbers,
				"overall_status" : overall_status,
				"approval_list_depts" : approval_list_depts,
				"current_pagination_option_id" : current_pagination_option_id,
				"current_page_num" : current_page_num,
			}
		else:
			context = {}
			messages.warning(request, f"This 4m form is already approved by {appr_elem.responded_user} on {serve.get_standard_str_format_of_dt_or_d(appr_elem.response_datetime)}")
	else:
		context = {}
		messages.warning(request, "your department approval is not raised for this 4m form")
	return render(request, 'a006/four_m_approval_view.html', context) 


@login_required(login_url="/accounts/login/")
def four_m_report(request):
    context = {
		"parent" : "reports",
		"segment" : "4M Report",	  
		"child" : "4M Report - Filter forms",	  
    }        
    return render(request, 'a006/four_m_report.html',context)


@login_required(login_url="/accounts/login/")
def four_m_report_view(request, form_id): 	 
	four_m_form = FourMFormModel.objects.get(id=form_id)
	mapped_items = FourMMapping.objects.filter(four_m_form_ref=form_id)	
	product_category_id = (mapped_items.first().mapped_i.icode//serve.IcodeSplitup.product_category["period"])*serve.IcodeSplitup.product_category["period"]
	mapped_items = mapped_items.values_list("mapped_i", flat=True)	
	mapped_items_values = list(mapped_items)
	product_models = Icodes.objects.filter(Q(icode__in=mapped_items_values) & Q(icode__in=serve.get_product_models(product_category_id=product_category_id))).order_by("icode")
	product_models = Icodes.objects.filter(Q(icode__in=mapped_items_values) & Q(icode__in=serve.get_product_models(product_category_id=product_category_id))).order_by("icode")
	production_lines = Icodes.objects.filter(Q(icode__in=mapped_items_values) & Q(icode__in=serve.get_production_lines(product_category_id=product_category_id))).order_by("icode")
	part_numbers = Icodes.objects.filter(Q(icode__in = mapped_items_values) & Q(icode__in=serve.get_part_numbers(product_category_id=product_category_id))).order_by("icode")
	child_part_numbers = {}
	if four_m_form.supplier_rel_chng:
		child_part_numbers = Icodes.objects.filter(Q(icode__in=mapped_items_values) & Q(icode__in=serve.get_child_part_numbers(product_category_id=product_category_id))).order_by("icode")	
	approval_list_depts = []
	for i in FourMApprovals.objects.filter(four_m_form_ref = four_m_form):
		if i.response is None:
			response = serve.st_pend_str
			responded_user = serve.na_str
			response_datetime = serve.na_str
			response_desc = serve.na_str
		else:
			response =  serve.st_appr_str if i.response else serve.st_rej_str
			response_datetime = i.response_datetime
			responded_user = serve.get_user_display_format(user=i.responded_user)
			response_desc = i.response_desc
		approval_list_depts.append([i.approval_needed_dept_i.name, responded_user, response, response_datetime, response_desc ])
	if four_m_form.fm_status is None:
		overall_status = serve.st_pend_str
	else:
		overall_status = serve.st_appr_str if four_m_form.fm_status else serve.st_rej_str						
	context = {
		"parent" : "reports",
		"segment" : "4M Report",	  
		"child" : "4M report - View",	  
		"four_m_form" : four_m_form,
		"xylem_code" : serve.xylem_code, 
		"app_name" : serve.an_4m_digitalization,       
		"production_lines" : production_lines,
		"product_models" : product_models,
		"part_numbers" : part_numbers,    
		"child_part_numbers" : child_part_numbers,
		"overall_status" : overall_status,
		"approval_list_depts" : approval_list_depts,       
	}
	return render(request, "a006/four_m_report_view.html", context)


@login_required(login_url="/accounts/login/")
def ajax_report_table(request):
	start_date = request.GET.get('from_date')
	end_date = request.GET.get('to_date')
	selected_status = request.GET.get('form_status')	
	start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
	end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
	four_m_forms = FourMFormModel.objects.filter(raised_datetime__date__range=[start_date, end_date])
	if selected_status == 'a':
		four_m_forms = four_m_forms.filter(fm_status=True)	
	elif selected_status == 'r':
		four_m_forms = four_m_forms.filter(fm_status=False)
	elif selected_status == 'p':
		four_m_forms = four_m_forms.filter(fm_status=None)	
	if not four_m_forms:
		messages.add_message(request, custom_messages.INFO_DISMISSABLE, mark_safe(f"No 4M Forms available for the selected dates and status"))
		return render(request, 'msg_templates/messages.html') 										
	context={
		"four_m_forms" : four_m_forms,
		"xylem_code" : serve.xylem_code, 
        "app_name" : serve.an_4m_digitalization, 		
	}
	return render(request, 'a006/ajax_report_table.html',context)	



if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
	pass
	# from . import xr_handler

elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
	pass

elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
	pass