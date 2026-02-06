import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse

import xylem.custom_messages.constants as custom_messages
from xylem_apps.a000_xylem_master.models import TPsMapping
from xylem_apps.a000_xylem_master import serve 
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom, view_eligibity_test
from xylem_apps.a006_4m_digitalization.models import FourMFormModel, FourMApprovals

from .tms_serve import get_tps_maps_with_low_life_by_pc, get_tps_map_list_with_param_by_pl_or_tool, get_tps_map_with_param
from .forms import ToolLifeBoostForm
from .models import ToolHistoryLog


# Create your views here.
@login_required(login_url="/accounts/login/")
def tool_cards(request, current_product_category_id, current_tool_type_id):
	product_categories=serve.get_product_categories()
	current_product_category=product_categories.get(icode=current_product_category_id)
	tool_types=serve.get_tool_types()
	current_tool_type=tool_types.get(icode=current_tool_type_id)
	tools = serve.get_tools(product_category=current_product_category)
	tool_cards_html = ""
	tool_avl_flag = tools.exists()
	mapping_avl_flag = None
	if tool_avl_flag:
		tools_in_type = serve.get_tools(product_category=current_product_category, tool_type_id=current_tool_type_id)
		if tools_in_type.exists():
			mapping_avl_flag = TPsMapping.objects.filter(tool_i__in = tools_in_type).exists()
			if mapping_avl_flag:
				tps_map_list = get_tps_maps_with_low_life_by_pc(product_category=current_product_category, tool_type=current_tool_type)
				tool_cards_html = render_to_string("a004/tool_cards_template.html", {"tps_map_list": tps_map_list, "current_tool_type": current_tool_type})
			else:
				messages.add_message(request, messages.INFO, f"No mapping is available for {current_tool_type.name}")
		else:
			messages.add_message(request, messages.INFO, f"No {current_tool_type.name} available in this product category")
	else:
		temp_list = [tool_type.name for tool_type in tool_types]
		messages.add_message(request, messages.INFO, f"No {', '.join(temp_list)} available in this product category")
	context = {
		"parent" : "projects",
		"segment" : "Tool Cards",
		"tool_avl_flag" : tool_avl_flag,
		"mapping_avl_flag": mapping_avl_flag,
		"tool_cards_html" : tool_cards_html,
		"current_product_category" : current_product_category,
		"product_categories" : product_categories,
		"current_tool_type" : current_tool_type,
		"tool_types" : tool_types,
	}
	return render(request,"a004/tool_cards.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.ME, serve.Designations.Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def tool_life_boost(request, tool_type_id, tps_map_id):
	tool_type = serve.get_icode_object(tool_type_id)
	tps_map = get_tps_map_with_param(tps_map_id=tps_map_id)
	form = ToolLifeBoostForm(request.POST or None, tps_map = tps_map)
	if request.method == "POST":
		if form.is_valid():
			four_m_form_ref_id = form.cleaned_data['four_m_form_ref_id']
			reason_for_change = form.cleaned_data['reason_for_change']
			action_taken = form.cleaned_data['action_taken']
			four_m_form_ref = FourMFormModel.objects.get(id=four_m_form_ref_id)  
			ToolHistoryLog.objects.create(
				tps_map = tps_map["tps_map"],
				boosted_change_over = tps_map["latest_cho"],
				reason_for_change = reason_for_change,
				four_m_form_ref = four_m_form_ref,
				pre_avl_life = tps_map["avl_tool_life"],
				produced_pq = tps_map["tps_map"].full_life - tps_map["avl_tool_life"],
				pq_offset = tps_map["ongoing_consumption"],
				action_taken = action_taken,
				boosted_user = request.user,
			)
			messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, mark_safe(f"The <b>{tps_map['tps_map'].tool_i.name}</b>\'s life boosted successfully"))
			return redirect("a004:tool_cards", current_product_category_id=serve.get_first_product_category().icode, current_tool_type_id=serve.get_first_tool_type().icode)
		else:	
			form.non_field_errors()	
	context = {		
		"parent" : "projects",
		"segment" : "Tool Cards",
		"child" : f"Tool Cards - {tool_type.name} - Boost Life",
		"tool_type" : tool_type,
		"tps_map" : tps_map,
		"form": form,
	}
	return render(request,'a004/tool_life_boost.html',context)


@login_required(login_url="/accounts/login/")
def tool_history_card(request, current_product_category_id, current_tool_type_id):
	product_categories = serve.get_product_categories()
	current_product_category = serve.get_icode_object(current_product_category_id)    
	pls = serve.get_production_lines_of_tools(product_category_id=current_product_category_id, tool_type_id=current_tool_type_id)  
	context = {
		"parent": "reports",
		"segment": "Tool History Card",
		"product_categories": product_categories,
		"current_product_category": current_product_category,     
		"tool_types": serve.get_tool_types,
		"current_tool_type": serve.get_icode_object(current_tool_type_id),
		"production_lines_drop_down_html": render_to_string('ajax_templates/drop_down_icodes.html', {'options': pls }) if pls.exists() else "",
	}
	return render(request,'a004/tool_history_card.html',context)


@login_required(login_url="/accounts/login/")
def ajax_tool_cards_of_tools_with_low_life(request):
	product_category_id = request.GET.get('product_category_id')
	tool_type_id = request.GET.get('tool_type_id')
	tps_map_list = get_tps_maps_with_low_life_by_pc(product_category_id=product_category_id, tool_type_id=tool_type_id)
	return render(request,"a004/tool_cards_template.html", {"tps_map_list": tps_map_list, "current_tool_type": serve.get_icode_object(tool_type_id)})


@login_required(login_url="/accounts/login/")
def ajax_tool_cards_of_pl(request):
	product_category_id = request.GET.get('product_category_id')
	tool_type_id = request.GET.get('tool_type_id')
	pl_or_tool_id = request.GET.get('pl_or_tool_id')
	context = {}
	if not pl_or_tool_id:
		pls_or_tools = serve.get_production_lines_of_tools(product_category_id=product_category_id, tool_type_id=tool_type_id)
		# if pls_or_tools
		pl_or_tool_id = pls_or_tools.first().icode
		context["pl_or_tool_selection_html"] = render_to_string("a004/pl_or_tool_selection.html", {
			"selection" : "Production Line",
			"pls_or_tools": pls_or_tools,
			"tool_type_id": tool_type_id
		})
	tps_map_list = get_tps_map_list_with_param_by_pl_or_tool(pl_or_tool_id=pl_or_tool_id, tool_type_id=tool_type_id)
	context["tool_cards_html"] = render_to_string("a004/tool_cards_template.html", {"tps_map_list": tps_map_list, "current_tool_type": serve.get_icode_object(tool_type_id)})
	return JsonResponse(context)


@login_required(login_url="/accounts/login/")
def ajax_tool_cards_of_tool(request):
	product_category_id = request.GET.get('product_category_id')
	tool_type_id = request.GET.get('tool_type_id')
	pl_or_tool_id = request.GET.get('pl_or_tool_id')
	context = {}
	if not pl_or_tool_id:
		pls_or_tools = serve.get_tools_of_tpss(product_category_id=product_category_id, tool_type_id=tool_type_id)
		pl_or_tool_id = pls_or_tools.first().icode
		context["pl_or_tool_selection_html"] = render_to_string("a004/pl_or_tool_selection.html", {
			"selection" : "Tool",
			"pls_or_tools": pls_or_tools,
			"tool_type_id": tool_type_id
		})
	tps_map_list = get_tps_map_list_with_param_by_pl_or_tool(pl_or_tool_id=pl_or_tool_id, tool_type_id=tool_type_id)
	context["tool_cards_html"] = render_to_string("a004/tool_cards_template.html", {"tps_map_list": tps_map_list, "current_tool_type": serve.get_icode_object(tool_type_id)})
	return JsonResponse(context)		


@login_required(login_url="/accounts/login/")
def ajax_tool_history_card(request):    
	production_station_id = request.GET.get('production_station_id')
	tool_id = request.GET.get('tool_id')
	from_date = request.GET.get('from_date')
	to_date = request.GET.get('to_date')
	from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d').date()
	to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d').date()      
	tps_map = TPsMapping.objects.get(production_station_i = production_station_id, tool_i = tool_id,)
	tool_history_data = ToolHistoryLog.objects.filter(tps_map = tps_map, boosted_time__date__gte = from_date, boosted_time__date__lte = to_date)   
	if not tool_history_data.exists():
		messages.add_message(request, custom_messages.INFO_DISMISSABLE, mark_safe(f"No tool replacements available for this time period"))
		return render(request, 'msg_templates/messages.html') 
	else:
		tool_history_data_list = []
		for tool_history in tool_history_data:
			fourm_appr = FourMApprovals.objects.get(four_m_form_ref=tool_history.four_m_form_ref,approval_needed_dept_i=serve.Depts.Inprocess_QA,response=True).responded_user
			tool_history_data_list.append({			
				'tool_history_data': tool_history,
				'fourm_responded_user': serve.get_user_display_format(user= fourm_appr)
			})
	return render(request,'a004/ajax_tool_history_card.html',
		{
			'tps_map': tps_map,
			'from_date': serve.get_standard_str_format_of_dt_or_d(d=from_date),
			'to_date': serve.get_standard_str_format_of_dt_or_d(d=to_date),
			'tool_history_data_with_qa_appr_list': tool_history_data_list
		}
	)	