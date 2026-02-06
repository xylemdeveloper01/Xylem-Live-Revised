import os, datetime, time, threading, queue, locale, uuid, random, logging, requests
from types import SimpleNamespace
from django.db.models import Max, Q, F
from django.db.utils import ProgrammingError
from django.db.models.query import QuerySet
from django.core.mail import EmailMultiAlternatives
from django.utils.safestring import mark_safe

from xylem.settings import XYLEM_MODE, XYLEM_MODE_DIC, EMAIL_HOST_USER

from .models import Icodes, UserProfile, MailDepartmentMapping, MailUserMapping, MailExternalmailidsMapping, UserPreventedMails, PnPrlPsMapping, PnMTMapping, PnCpnMapping,\
	PatrolCheckSheets, OeDMapping, PnPrlCtData, TPsMapping, TPsmapPnExMapping, PyPsMapping, OEEProductionLineSetting, UnsentMails,WorkflowForms

xylem_code = "X"

mail_handler_log_name = "mail_handler"
xylem_remote_handler_log_name = "xylem_remote_handler"

na_str = "NA"
st_appr_str = "Approved"
st_rej_str = "Rejected"
st_pend_str = "Pending"

format_of_shift_time = "%H:%M:%S"
format_of_break_time = "%M:%S"
format_of_hour = "%H:%M"

# it will ensure low life consideration of a tool should falls below percenrage limit of full tool life
low_life_consideration_thresold_start_percent_from_full_life = 5
low_life_consideration_thresold_end_percent_from_full_life = 25

a009_pc_dashboard_day_cum_name = "Day Overview"
a009_pc_dashboard_month_cum_name = "Month Overview"
a009_pc_dashboard_income_eb_cum_name = "Income Water Supply"
a009_pc_dashboard_income_dg_cum_name = "Income Water Supply"


a009_wc_dashboard_day_cum_name = "Day Overview"
a009_wc_dashboard_month_cum_name = "Month Overview"
a009_wc_dashboard_income_cum_name = "Income Water Supply"
a009_wc_dashboard_section1_name = "Canteen"
a009_wc_dashboard_section2_name = "Rest Rooms - Shop Floor 1"
a009_wc_dashboard_section3_name = "Rest Rooms - Shop Floor 2"
a009_wc_dashboard_section1_bg_color = "#1de9b6"
a009_wc_dashboard_section2_bg_color = "#899FD4"
a009_wc_dashboard_section3_bg_color = "#04a9f5"

qa_qcs_dict = {
	"extra_columns" : {
		"operator_col":{
			"col_index":1,
			"name": "OPERATOR NAME"
		},
		"inspection_col":{
			"col_index":5,
			"name": "INSPECTION RESULT"
		},
	},
	"operator_input_element_name" : "op_inp_elem",
	"inspection_input_element_name" : "insp_inp_elem",
	"operator_input_elements_max" : 50,
	"inspection_input_elements_max" : 200,
	"inspection_input_element_max_len" : 30,
}
qa_pcs_extra_columns = qa_qcs_dict["extra_columns"]
qa_pcs_operator_input_element_name = qa_qcs_dict["operator_input_element_name"]
qa_pcs_inspection_input_element_name = qa_qcs_dict["inspection_input_element_name"]
qa_pcs_operator_input_elements_max = qa_qcs_dict["operator_input_elements_max"]
qa_pcs_inspection_input_elements_max = qa_qcs_dict["inspection_input_elements_max"]
qa_pcs_inspection_input_element_max_len = qa_qcs_dict["inspection_input_element_max_len"]

max_number_of_events_added_a008 = 3

soc_a000_data_pack_size_byte_len = 2
soc_a000_data_pack_size_byte_len_byte = soc_a000_data_pack_size_byte_len.to_bytes(1,'big')
soc_a000_where_id_byte_len = 4
soc_a000_where_id_byte_len_byte = soc_a000_where_id_byte_len.to_bytes(1,'big')
soc_a000_what_id_byte_len = 4
soc_a000_what_id_byte_len_byte = soc_a000_what_id_byte_len.to_bytes(1,'big')
soc_a000_unique_no_byte_len = 2
soc_a000_unique_no_byte_len_byte = soc_a000_unique_no_byte_len.to_bytes(1,'big')

soc_a000_prod_data_sign = 1
soc_a000_prod_data_sign_byte = soc_a000_prod_data_sign.to_bytes(1,'big')

soc_a000_production_interrupt_sign = 2
soc_a000_production_interrupt_sign_byte = soc_a000_production_interrupt_sign.to_bytes(1,'big')
soc_a000_production_interrupt_sign_up = 1
soc_a000_production_interrupt_sign_up_byte = soc_a000_production_interrupt_sign_up.to_bytes(1,'big')
soc_a000_production_interrupt_sign_down = 2
soc_a000_production_interrupt_sign_down_byte = soc_a000_production_interrupt_sign_down.to_bytes(1,'big')

soc_a000_dept_passwords_sign = 3
soc_a000_dept_passwords_sign_byte = soc_a000_dept_passwords_sign.to_bytes(1,'big')
soc_a000_dept_passwords_sign_qa = 1
soc_a000_dept_passwords_sign_qa_byte = soc_a000_dept_passwords_sign_qa.to_bytes(1,'big')
soc_a000_dept_passwords_sign_mfg = 2
soc_a000_dept_passwords_sign_mfg_byte = soc_a000_dept_passwords_sign_mfg.to_bytes(1,'big')
soc_a000_dept_passwords_sign_ple = 3
soc_a000_dept_passwords_sign_ple_byte = soc_a000_dept_passwords_sign_ple.to_bytes(1,'big')
soc_a000_dept_passwords_sign_me = 4
soc_a000_dept_passwords_sign_me_byte = soc_a000_dept_passwords_sign_me.to_bytes(1,'big')

soc_a007_oee_eve_cap_sign = 4
soc_a007_oee_eve_cap_sign_byte = soc_a007_oee_eve_cap_sign.to_bytes(1,'big')
soc_a007_oee_eve_cap_sign_popup = 1
soc_a007_oee_eve_cap_sign_popup_byte = soc_a007_oee_eve_cap_sign_popup.to_bytes(1,'big')
soc_a007_oee_eve_cap_sign_popdown = 2
soc_a007_oee_eve_cap_sign_popdown_byte = soc_a007_oee_eve_cap_sign_popdown.to_bytes(1,'big')

soc_a007_manu_com_sign = 5
soc_a007_manu_com_sign_byte = soc_a007_manu_com_sign.to_bytes(1,'big')

soc_a007_test_oee_eve_id_chat_sign = 6
soc_a007_test_oee_eve_id_chat_sign_byte = soc_a007_test_oee_eve_id_chat_sign.to_bytes(1,'big')

soc_a009_process_data_sign = 7
soc_a009_process_data_sign_byte = soc_a009_process_data_sign.to_bytes(1,'big')
soc_a009_process_data_sign_ok = 1
soc_a009_process_data_sign_ok_byte = soc_a009_process_data_sign_ok.to_bytes(1,'big')
soc_a009_process_data_sign_nok = 2
soc_a009_process_data_sign_nok_byte = soc_a009_process_data_sign_nok.to_bytes(1,'big')

# production interrupt messages maximum 254 characters will only pass
a007_production_interrupt_msg = "Kindly enter oee loss under ==> HOME --> XYLEM --> OEE --> ... "

max_byte_len_of_production_interrupt_msg = 254 # maximum is 255
max_byte_len_of_dept_password = 10 # maximum is 255

a007_production_interrupt_msg_byte = a007_production_interrupt_msg.encode()[:max_byte_len_of_production_interrupt_msg]

# Bootstrap Colors
bs_primary_color = "#007BFF"
bs_secondary_color = "#6C757D"
bs_success_color = "#28A745"
bs_info_color = "#17A2B8"
bs_warning_color = "#FFC107"
bs_danger_color = "#DC3545"
bs_light_color = "#F8F9FA"
bs_dark_color = "#343A40"

# maximum is 10 characters
a000_qa_password = "new_qa" 
a000_mfg_password = "newmfg"
a000_ple_password = "new_ple"
a000_me_password = "new_me"

percent_mid_start = 50
percent_high_start = 80

percent_low_bg_color = bs_danger_color
percent_mid_bg_color = bs_warning_color
percent_high_bg_color = bs_success_color

# percent_low_bg_color = "#DC3545"
# percent_mid_bg_color = "#FFC107"
# percent_high_bg_color = "#28A745"

percent_low_txt_color = "#FFFFFF"
percent_mid_txt_color = "#000000"
percent_high_txt_color = "#FFFFFF"

loss_bg_color = "#800000"
loss_txt_color = "#FFFFFF"


# pc_lbc : percent low background color, pc_ltc : percent low text color, pc_lst : percent low symbol text, pc_lt : percent low text
# pc_mbc : percent medium background color, pc_mtc : percent medium text color, pc_mst : percent medium symbol text, pc_mt : percent medium text
# pc_hbc : percent high background color, pc_htc : percent high text color, pc_hst : percent high symbol text, pc_ht : percent high text
# pc_ll : percent low limit, pc_ml : percent medium limit

color_code_dict = {
	"pc_lbc": percent_low_bg_color,
	"pc_ltc": percent_low_txt_color,
	"pc_lst": f"<{percent_mid_start}%",
	"pc_lt": f"Below {percent_mid_start}%",
	"pc_mbc": percent_mid_bg_color,
	"pc_mtc": percent_mid_txt_color,
	"pc_mst": f">={percent_mid_start}%,<{percent_high_start}%",
	"pc_mt": f"{percent_mid_start}% and above, below {percent_high_start}%",
	"pc_hbc": percent_high_bg_color,
	"pc_htc": percent_high_txt_color,
	"pc_hst": f">={percent_high_start}%",
	"pc_ht": f"{percent_high_start}% and above",
	"pc_ll": percent_mid_start,
	"pc_ml": percent_high_start,
}

a009_fm_inflow_from_id = 10
a009_fm_inflow_to_id = 19
a009_fm_outflow_from_id = 20
a009_fm_outflow_to_id = 29

mail_handler_logger = logging.getLogger(mail_handler_log_name)


class IcodeSplitup:
	part_status = { "from": 0, "to": 5 }
	shift = { "from": 11, "to": 13 }
	icode_shiftA = 11
	icode_shiftB = 12
	icode_shiftC = 13
	genders = { "from": 16, "to": 18 }
	yes_no_options = { "from": 8, "to": 9 }
	cs_status_type_options = { "from": 36, "to": 38 }
	approval_mode_options = { "from": 41, "to": 43 }
	wf_status_type_options = { "from": 46, "to": 49 }
	tool_type_options = { "from": 23, "to": 24 }
	tool_change_reasons = { "from": 25, "to": 26 }
	pn_drawing_status_options = { "from": 55, "to": 57 }
	plant_locations = { "from": 101, "to": 120 }
	depts  = { "from": 121, "to": 140 }
	designations  = { "from": 141, "to": 160 }
	flow_meters  = { "from": 161, "to": 260 }
	poka_yoke_criticality_levels  = { "from": 261, "to": 270 }
	pagination_options  = { "from": 271, "to": 280 }
	apps  = { "from": 300, "to": 399 }
	mails  = { "from": 400, "to": 699 }
	barcode_avl_types  = { "from": 5, "to": 6 }
	product_category  = { "from": 500000 , "period": 500000}
	product_technologies  = { "from_in_category": 1, "to_in_category": 99 }
	production_lines  = { "from_in_category": 100000, "to_in_category": 199999, "period_in_category": 100 }
	product_models  = { "from_in_category": 500, "to_in_category": 999 }
	part_numbers  = { "from_in_category": 1000, "to_in_category": 9999 }
	child_part_numbers  = { "from_in_category": 10000, "to_in_category": 99999 }
	rejection_reasons  = { "from_in_category": 200000, "to_in_category": 205000 }
	tool_tools = { "from_in_category": 250001, "to_in_category": 251000 }
	tool_fixtures = { "from_in_category": 251001, "to_in_category": 252000 }
	poka_yokes = { "from_in_category": 252001, "to_in_category": 254000 }
	four_m_ponits  = { "from": 19, "to": 22 }
	hmi_production_interrupt_msgs = { "from": 9900, "to": 9990 }
	manu_com_alerts = { "from": 9991, "to": 10000 }
	oee_events = { "from": 10001, "to": 60000 }


def remove_space(string):
	if string:
		return string.replace(" ", "")
	return string


def generate_uuid_token32():
	return uuid.uuid4().hex


def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def first_n_primes(n):
    primes = []
    num = 2  # Starting point for prime search
    while len(primes) < n:
        if is_prime(num):
            primes.append(num)
        num += 1
    return primes


# number with comma indian format
locale.setlocale(locale.LC_ALL, 'English_India.1252')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'
def get_number_with_comma(number):
	temp_list = str(number).split(".")
	try:
		temp_list[0] = f'{int(temp_list[0]):n}'
	except:
		pass
	return ".".join(temp_list)


def get_all_users():
	return UserProfile.objects.filter(is_active=True)


def get_user_object(id):
	return UserProfile.objects.get(id=int(id))


def get_user_object(id):
	return UserProfile.objects.get(id=int(id))


def get_user_object_by_mail(mail):
	return UserProfile.objects.get(email=mail)


def get_user_display_format(user = None, user_id = None, with_dept = None):
	if user_id:
		user = get_user_object(user_id)
	return f"{user.username} - {user.first_name} {user.last_name}" if with_dept is None else f"{user.username} - {user.first_name} {user.last_name} ({user.dept_i.description})"


def get_doc_format_number_with_rev_number_and_date_as_list(app): # get document format number, revision number and revision_date
	pass


def get_pl_ps_display_format(production_station = None, production_station_id = None):  # get production line of production station
	if production_station_id:
		production_station=get_icode_object(production_station_id)
	return get_production_line_of_ps(production_station=production_station).name + " - " + production_station.name


def get_mails_of_user(user = None, user_id = None): # get mails of user
	if user_id:
		user = get_user_object(user_id)
	return Icodes.objects.filter(
		Q(icode__in = MailUserMapping.objects.filter(user=user).values_list("mail_i_id", flat=True).distinct()) |
		Q(icode__in = MailDepartmentMapping.objects.filter(dept=user.dept_i).values_list("mail_i_id", flat=True).distinct())
	)


def get_mail_ids_list_of_dept(dept = None, dept_id = None):
	if dept:
		dept_id = dept.icode
	dept_id = int(dept_id)
	return list(UserProfile.objects.filter(is_active=True, dept_i_id=dept_id, email__endswith='@ranegroup.com').exclude().values_list('email', flat=True))


def get_mail_ids_list_of_mail(mail = None, mail_icode = None): # get mail ids by mail
	if mail:
		mail_icode = mail.icode
	mail_icode = int(mail_icode)
	mail_id_list = []
	dept_id_list = MailDepartmentMapping.objects.filter(mail_i_id=mail_icode).values_list('dept_id', flat=True).distinct()
	if XYLEM_MODE != XYLEM_MODE_DIC["deployment_mode"]:
		dept_id_list = [Depts.Development_team.icode]
	for dept_id in dept_id_list:
		mail_id_list = mail_id_list + get_mail_ids_list_of_dept(dept_id=dept_id)
	mail_id_list = mail_id_list + list(MailUserMapping.objects.filter(mail_i_id=mail_icode).values_list('user__email', flat=True).distinct())
	mail_id_list = mail_id_list + list(MailExternalmailidsMapping.objects.filter(mail_i_id=mail_icode).values_list('external_mail_id', flat=True).distinct())
	excluded_mail_id_list = list(UserPreventedMails.objects.filter(mail_i_id=mail_icode).values_list('user__email', flat=True).distinct())
	mail_id_list = [mail_id for mail_id in mail_id_list if mail_id not in excluded_mail_id_list]
	return mail_id_list


def get_mail_prevented_status_of_user(mail = None, mail_icode = None, user = None, user_id = None): # get mail prevented status of user
	if user:
		user_id = user.id
	user_id = int(user_id)
	if mail:
		mail_icode = mail.icode
	mail_icode = int(mail_icode)
	return UserPreventedMails.objects.filter(user_id=user_id, mail_i_id=mail_icode).exists()


def get_mail_list_of_four_m_app_mail(dept_i = None, dept_id = None):
    if dept_i:
        dept_id = dept_i.icode
    dept_id = int(dept_id)
    return list(UserProfile.objects.filter(is_active=True, designation_i__gte=Designations.Assistant_Manager,dept_i_id=dept_id, email__endswith='@ranegroup.com').values_list('email', flat=True))


def get_icode_none_object():
	return Icodes.objects.none()


def get_icode_not_defined_object():
	return Icodes.objects.get_or_create(icode=IcodeSplitup.icode_not_defined["icode"], name=IcodeSplitup.icode_not_defined["name"])


def get_icode_object(icode):
	try:
		return Icodes.objects.get(icode=int(icode))
	except (ProgrammingError, Icodes.DoesNotExist) as e :
		return Icodes(icode=icode, name=na_str, description=na_str)


def get_icode_objects(icode_list):
	for index_i,i in enumerate(icode_list):
		icode_list[index_i] = int(i)
	return Icodes.objects.filter(icode__in=icode_list).order_by('icode')


def get_genders():
	return Icodes.objects.filter(icode__gte=IcodeSplitup.genders['from'], icode__lte=IcodeSplitup.genders['to']).order_by("icode")


def get_shifts():
	return Icodes.objects.filter(icode__gte=IcodeSplitup.shift['from'], icode__lte=IcodeSplitup.shift['to']).order_by("icode")


def get_plant_locations():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.plant_locations['from'], icode__lte=IcodeSplitup.plant_locations['to'])).order_by("icode")


def get_depts():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.depts['from'], icode__lte=IcodeSplitup.depts['to'])).order_by("icode")


def get_flow_meters():
	# return Icodes.objects.filter(icode__gte=IcodeSplitup.flow_meters['from'], icode__lte=IcodeSplitup.flow_meters['to']).order_by("icode")
	return Icodes.objects.filter(icode__gte=IcodeSplitup.flow_meters['from'], icode__lte=IcodeSplitup.flow_meters['to']).order_by("icode").exclude(icode__in=[166]) # do change in others class flowmeter list also


def get_poka_yoke_criticality_levels():
	return Icodes.objects.filter(icode__gte=IcodeSplitup.poka_yoke_criticality_levels['from'], icode__lte=IcodeSplitup.poka_yoke_criticality_levels['to']).order_by("icode")


def get_pagination_options():
	return Icodes.objects.filter(icode__gte=IcodeSplitup.pagination_options['from'], icode__lte=IcodeSplitup.pagination_options['to']).order_by("icode")


def get_first_pagination_option():
	return get_pagination_options().first()


def get_pn_drawing_status_options():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.pn_drawing_status_options['from'], icode__lte=IcodeSplitup.pn_drawing_status_options['to'])).order_by("icode")


def get_first_pn_drawing_status_option():
	return get_pn_drawing_status_options().first()


def get_dept_of_oee_event(oee_event = None, oee_event_id = None):
	if oee_event_id:
		oee_event = get_icode_object(oee_event_id)
	return oee_event.wi_oed_m.dept_i


def get_designations():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.designations['from'], icode__lte=IcodeSplitup.designations['to'])).order_by("icode")


def get_barcode_avl_types():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.barcode_avl_types['from'], icode__lte=IcodeSplitup.barcode_avl_types['to'])).order_by("icode")


def get_yes_no_options():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.yes_no_options['from'], icode__lte=IcodeSplitup.yes_no_options['to'])).order_by("icode")


def get_checksheets_status_types():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.cs_status_type_options['from'], icode__lte=IcodeSplitup.cs_status_type_options['to'])).order_by("icode")


def get_approval_modes():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.approval_mode_options['from'], icode__lte=IcodeSplitup.approval_mode_options['to'])).order_by("icode")


def get_worflows_status_types():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.wf_status_type_options['from'], icode__lte=IcodeSplitup.wf_status_type_options['to'])).order_by("icode")


def get_checksheets_first_status_type():
	return get_checksheets_status_types().first()


def get_worflows_first_status_type():
	return get_worflows_status_types().first()


def get_tool_types():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.tool_type_options['from'], icode__lte=IcodeSplitup.tool_type_options['to'])).order_by("icode")


def get_first_tool_type():
	return get_tool_types().first()


def get_tool_type_by_tool(tool = None, tool_id = None): # get tool type by tool 
	if tool:
		tool_id = tool.icode
	tool_id = int(tool_id)
	product_category_id = get_product_category_by_item(item_id=tool_id).icode
	return Others.tool_tools if product_category_id + IcodeSplitup.tool_tools["from_in_category"]<=tool_id and  product_category_id + IcodeSplitup.tool_tools["to_in_category"]>=tool_id else Others.tool_fixtures


def get_tool_change_reasons():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.tool_change_reasons['from'], icode__lte=IcodeSplitup.tool_change_reasons['to'])).order_by("icode")


def get_product_categories():
	return Icodes.objects.filter(
		icode__gte=IcodeSplitup.product_category["from"],
		icode=F('icode')-((F('icode')-IcodeSplitup.product_category["from"])%IcodeSplitup.product_category['period'])
	).order_by("icode")


def get_first_product_category():
	return get_product_categories().first()


def get_product_category_by_item(item = None, item_id = None):
	if item:
		item_id = item.icode
	item_id = int(item_id)
	return Icodes.objects.get(icode = (item_id-(item_id-IcodeSplitup.product_category["from"])%IcodeSplitup.product_category["period"]))


def get_product_technologies(product_category = None, product_category_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	return Icodes.objects.filter(
		icode__gte=product_category_id+IcodeSplitup.product_technologies["from_in_category"],
		icode__lte=product_category_id+IcodeSplitup.product_technologies["to_in_category"]
	).order_by("icode")


def get_product_models(product_category = None, product_category_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	return Icodes.objects.filter(
		icode__gte=product_category_id+IcodeSplitup.product_models["from_in_category"],
		icode__lte=product_category_id+IcodeSplitup.product_models["to_in_category"]
	).order_by("icode")


def get_product_models_of_pl(production_line = None, production_line_id = None): # get product models by production line
	if production_line:
		production_line_id=production_line.icode
	production_line_id = int(production_line_id)
	return Icodes.objects.filter(
		icode__in = PnMTMapping.objects.filter(
			part_number_i_id__in=PnPrlPsMapping.objects.filter(
				production_line_i_id=production_line_id
			).values_list("part_number_i").distinct()
		).values_list("model_i").distinct()
	).order_by("icode")


def get_product_models_of_ps(production_station = None, production_station_id = None): # get product models by production station
    if production_station:
        production_station_id=production_station.icode
    production_station_id = int(production_station_id)
    return Icodes.objects.filter(
        icode__in = PnMTMapping.objects.filter(
            part_number_i_id__in=PnPrlPsMapping.objects.filter(
                production_station_i_id=production_station_id
            ).values_list("part_number_i").distinct()
        ).values_list("model_i").distinct()
    ).order_by("icode")



def get_product_models_of_pls(production_line_list =  None, production_line_id_list = None): # get product models by production lines
	production_line_list =  production_line_list or []
	production_line_id_list =  production_line_id_list or []
	if production_line_list:
		for production_line in production_line_list: 
			production_line_id_list.append(production_line.icode)
	for index_i,i in enumerate(production_line_id_list):
		production_line_id_list[index_i] = int(i)
	return Icodes.objects.filter(
		icode__in = PnMTMapping.objects.filter(
			part_number_i_id__in=PnPrlPsMapping.objects.filter(
				production_line_i_id__in=production_line_id_list
			).values_list("part_number_i").distinct()
		).values_list("model_i").distinct()
	).order_by("icode")


def get_product_models_of_qa_pcs(product_category = None, product_category_id = None, alive_flag = None): # get product models from quality patrol checksheet
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	if not alive_flag is None:
		return Icodes.objects.filter(
			icode__in = PnMTMapping.objects.filter(
				part_number_i_id__in=PatrolCheckSheets.objects.filter(
					production_line_i_id__gte=product_category_id+IcodeSplitup.production_lines["from_in_category"],
					production_line_i_id__lte=product_category_id+IcodeSplitup.production_lines["to_in_category"],
					alive_flag = alive_flag,
				).values_list("part_number_i").distinct()
			).values_list("model_i").distinct()
		).order_by("icode")
	return Icodes.objects.filter(
		icode__in = PnMTMapping.objects.filter(
			part_number_i_id__in=PatrolCheckSheets.objects.filter(
				production_line_i_id__gte=product_category_id+IcodeSplitup.production_lines["from_in_category"],
				production_line_i_id__lte=product_category_id+IcodeSplitup.production_lines["to_in_category"],
			).values_list("part_number_i").distinct()
		).values_list("model_i").distinct()
	).order_by("icode")


def get_product_models_of_pl_qa_pcs(production_line = None, production_line_id = None, alive_flag = None): # get product models from quality patrol checksheet of a line
	if production_line:
		production_line_id = production_line.icode
	production_line_id = int(production_line_id)
	if not alive_flag is None:
		return Icodes.objects.filter(
			icode__in = PnMTMapping.objects.filter(
				part_number_i_id__in=PatrolCheckSheets.objects.filter(
					production_line_i_id=production_line_id,
					alive_flag = alive_flag,
				).values_list("part_number_i").distinct()
			).values_list("model_i").distinct()
		).order_by("icode")
	return Icodes.objects.filter(
		icode__in = PnMTMapping.objects.filter(
			part_number_i_id__in=PatrolCheckSheets.objects.filter(
				production_line_i_id=production_line_id,
			).values_list("part_number_i").distinct()
		).values_list("model_i").distinct()
	).order_by("icode")


def get_production_lines(product_category = None, product_category_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	return Icodes.objects.filter(
		icode__gte=product_category_id+IcodeSplitup.production_lines["from_in_category"],
		icode__lte=product_category_id+IcodeSplitup.production_lines["to_in_category"],
		icode=F('icode')-F('icode')%IcodeSplitup.production_lines['period_in_category']
	).order_by("icode")


def get_production_lines_of_tech(technology = None, technology_id = None): # get production lines by technology
	if technology:
		technology_id = technology.icode
	technology_id = int(technology_id)
	return Icodes.objects.filter(
		icode__in=PnPrlPsMapping.objects.filter(part_number_i_id__in=
			PnMTMapping.objects.filter(
				technology_i_id = technology_id
			).values_list("part_number_i").distinct()
		).values_list("production_line_i").distinct()
	).order_by("icode")


def get_production_lines_of_pn(part_number = None, part_number_id = None): # get production lines by part number
	if part_number:
		part_number_id = part_number.icode
	part_number_id = int(part_number_id)
	return Icodes.objects.filter(
		icode__in=PnPrlPsMapping.objects.filter(part_number_i_id=part_number_id).values_list("production_line_i").distinct()
	).order_by("icode")


def get_production_lines_of_model(model = None, model_id = None): # get production lines by model
	if model:
		model_id = model.icode
	model_id = int(model_id)
	return Icodes.objects.filter(
		icode__in = PnPrlPsMapping.objects.filter(
			part_number_i_id__in=PnMTMapping.objects.filter(
				model_i_id=model_id
			).values_list("part_number_i").distinct()
		).values_list("production_line_i").distinct()
	).order_by("icode")


def get_production_line_of_ps(production_station = None, production_station_id = None):  # get production line of production station
	if production_station:
		production_station_id=production_station.icode
	production_station_id = int(production_station_id)
	temp_reminder = (production_station_id-IcodeSplitup.product_category["from"])%IcodeSplitup.product_category['period']
	product_category_id = production_station_id-temp_reminder
	temp_quotient = (temp_reminder-IcodeSplitup.production_lines["from_in_category"])//IcodeSplitup.production_lines["period_in_category"]
	production_line_id = product_category_id+IcodeSplitup.production_lines["from_in_category"]+temp_quotient*IcodeSplitup.production_lines["period_in_category"]
	return get_icode_object(production_line_id)


def get_production_lines_of_pss(production_station_list =  None, production_station_id_list = None):  # get production lines of production stations
	production_station_list =  production_station_list or []
	production_station_id_list =  production_station_id_list or []
	if production_station_list:
		for production_station in production_station_list: 
			production_station_id_list.append(production_station.icode)
	for index_i,i in enumerate(production_station_id_list):
		production_station_id_list[index_i] = int(i)
	production_line_list = []
	for ps_id in production_station_id_list:
		pl = get_production_line_of_ps(production_station_id=ps_id)
		if not pl.icode in production_line_list:
			production_line_list.append(pl.icode)
	return Icodes.objects.filter(icode__in = production_line_list).order_by("icode")
  

def get_production_lines_of_qa_pcss(product_category = None, product_category_id = None, alive_flag = None): # get production lines of quality patrol checksheets
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	if not alive_flag is None:
		return Icodes.objects.filter(
			icode__in = PatrolCheckSheets.objects.filter(
				production_line_i_id__gte=product_category_id+IcodeSplitup.production_lines["from_in_category"],
				production_line_i_id__lte=product_category_id+IcodeSplitup.production_lines["to_in_category"],
				alive_flag = alive_flag,
			).values_list("production_line_i").distinct()
		).order_by("icode")  
	return Icodes.objects.filter(
		icode__in = PatrolCheckSheets.objects.filter(
			production_line_i_id__gte=product_category_id+IcodeSplitup.production_lines["from_in_category"],
			production_line_i_id__lte=product_category_id+IcodeSplitup.production_lines["to_in_category"],
		).values_list("production_line_i").distinct()
	).order_by("icode")


def get_workflows_fms(status_flag=None): # get workflows forms
    wf = WorkflowForms.objects.all()
    if status_flag is not None:
        wf = wf.filter(status_flag=status_flag)
    return wf.order_by("form_name")


def get_production_lines_of_tools(product_category = None, product_category_id = None, tool_type = None, tool_type_id = None): # get production lines of tools
	pss = TPsMapping.objects.filter(tool_i__in=get_tools(product_category=product_category, product_category_id=product_category_id, tool_type=tool_type, tool_type_id = tool_type_id)).values_list('production_station_i', flat=True).distinct()
	pl_id_list = []
	for ps in pss:
		pl_id = get_production_line_of_ps(production_station_id=ps).icode
		if not pl_id in pl_id_list:
			pl_id_list.append(pl_id)
	return Icodes.objects.filter(
		icode__in = pl_id_list
	).order_by("icode")


def get_production_lines_of_oee_enabled(product_category = None, product_category_id = None): # get production lines of oee enabled
	if product_category is None and product_category_id is None:
		return Icodes.objects.filter(opls_pl__isnull=False)
	return get_production_lines(product_category = product_category, product_category_id = product_category_id).filter(opls_pl__isnull=False)


def get_production_stations(production_line = None, production_line_id = None):
	if production_line:
		production_line_id=production_line.icode
	production_line_id = int(production_line_id)
	return Icodes.objects.filter(
		icode__gt=production_line_id,
		icode__lt=production_line_id+ IcodeSplitup.production_lines['period_in_category']
	).order_by("icode")


def get_production_stations_of_pl_tools(production_line = None, production_line_id = None, tool_type = None, tool_type_id = None): # get production stations of production line and tools 
	if production_line:
		production_line_id = production_line.icode
	production_line_id = int(production_line_id)
	if tool_type:
		tool_type_id = tool_type.icode
	tool_type_id = int(tool_type_id)
	product_category_id = get_product_category_by_item(item_id=production_line_id).icode
	if tool_type_id == Others.tool_tools.icode:
		return Icodes.objects.filter(
			icode__in = TPsMapping.objects.filter(
				tool_i_id__gte=product_category_id+IcodeSplitup.tool_tools["from_in_category"],
				tool_i_id__lte=product_category_id+IcodeSplitup.tool_tools["to_in_category"],
				production_station_i_id__gte=production_line_id,
				production_station_i_id__lte=production_line_id + IcodeSplitup.production_lines['period_in_category'],
			).values_list("production_station_i").distinct()
		).order_by("icode")  
	return Icodes.objects.filter(
		icode__in = TPsMapping.objects.filter(
			tool_i_id__gte=product_category_id+IcodeSplitup.tool_fixtures["from_in_category"],
			tool_i_id__lte=product_category_id+IcodeSplitup.tool_fixtures["to_in_category"],
				production_station_i_id__gte=production_line_id,
			production_station_i_id__lte=production_line_id + IcodeSplitup.production_lines['period_in_category'],
		).values_list("production_station_i").distinct()
	).order_by("icode")
	

def get_part_numbers(product_category = None, product_category_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	return Icodes.objects.filter(
		icode__gte=product_category_id+IcodeSplitup.part_numbers["from_in_category"],
		icode__lte=product_category_id+IcodeSplitup.part_numbers["to_in_category"]
	).order_by("icode")


def get_part_numbers_of_tech(technology = None, technology_id = None):  # get part numbers by technology
	if technology:
		technology_id=technology.icode
	technology_id = int(technology_id)
	return Icodes.objects.filter(
		icode__in = PnMTMapping.objects.filter(
			technology_i_id=technology_id
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_part_numbers_of_model(model = None, model_id = None):  # get part numbers by model
	if model:
		model_id=model.icode
	model_id = int(model_id)
	return Icodes.objects.filter(
		icode__in = PnMTMapping.objects.filter(
			model_i_id=model_id
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_part_numbers_of_models(model_list = None, model_id_list = None):  # get part numbers by models
	model_list =  model_list or []
	model_id_list =  model_id_list or []
	if model_list:
		for model in model_list: 
			model_id_list.append(model.icode)
	for index_i,i in enumerate(model_id_list):
		model_id_list[index_i] = int(i)
	return Icodes.objects.filter(
		icode__in = PnMTMapping.objects.filter(
			model_i_id__in=model_id_list
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_part_numbers_of_pl(production_line = None, production_line_id = None):  # get part numbers by production line
	if production_line:
		production_line_id=production_line.icode
	production_line_id = int(production_line_id)
	return Icodes.objects.filter(
		icode__in=PnPrlPsMapping.objects.filter(
			production_line_i_id=production_line_id
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_part_numbers_of_pls(production_line_list = None, production_line_id_list = None):  # get part numbers by production lines
	production_line_list =  production_line_list or []
	production_line_id_list =  production_line_id_list or []
	if production_line_list:
		for production_line in production_line_list: 
			production_line_id_list.append(production_line.icode)
	for index_i,i in enumerate(production_line_id_list):
		production_line_id_list[index_i] = int(i)
	return Icodes.objects.filter(
		icode__in=PnPrlPsMapping.objects.filter(
			production_line_i_id__in=production_line_id_list
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_part_numbers_of_ps(production_station = None, production_station_id = None):  # get part numbers by production station
	if production_station:
		production_station_id=production_station.icode
	production_station_id = int(production_station_id)
	return Icodes.objects.filter(
		icode__in=PnPrlPsMapping.objects.filter(
			production_station_i_id=production_station_id
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_part_numbers_of_qa_pcs(product_category = None, product_category_id = None, alive_flag = None): # get part numbers from quality patrol checksheet
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	if not alive_flag is None:
		return Icodes.objects.filter(
			icode__in = PatrolCheckSheets.objects.filter(
				part_number_i_id__gte=product_category_id+IcodeSplitup.part_numbers["from_in_category"],
				part_number_i_id__lte=product_category_id+IcodeSplitup.part_numbers["to_in_category"],
				alive_flag = alive_flag,
			).values_list("part_number_i").distinct()
		).order_by("icode")  
	return Icodes.objects.filter(
		icode__in = PatrolCheckSheets.objects.filter(
			part_number_i_id__gte=product_category_id+IcodeSplitup.production_lines["from_in_category"],
			part_number_i_id__lte=product_category_id+IcodeSplitup.production_lines["to_in_category"],
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_part_numbers_of_pl_qa_pcs(production_line = None, production_line_id = None, alive_flag = None): # get part numbers from quality patrol checksheet of a production line
	if production_line:
		production_line_id = production_line.icode
	production_line_id = int(production_line_id)
	if not alive_flag is None:
		return Icodes.objects.filter(
			icode__in = PatrolCheckSheets.objects.filter(
				production_line_i_id=production_line_id,
				alive_flag = alive_flag,
			).values_list("part_number_i").distinct()
		).order_by("icode")  
	return Icodes.objects.filter(
		icode__in = PatrolCheckSheets.objects.filter(
			production_line_i_id=production_line_id
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_part_numbers_of_tps(tps_map = None, tps_map_id = None):  # get part numbers by production station
	if tps_map_id:
		tps_map = TPsMapping.objects.get(tps_map_id)
	return get_part_numbers_of_ps(production_station=tps_map.production_station_i).exclude(
		icode__in=TPsmapPnExMapping.objects.filter(
			tps_map=tps_map
		).values_list("part_number_i").distinct()
	).order_by("icode")


def get_child_part_numbers(product_category = None, product_category_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	return Icodes.objects.filter(
		icode__gte=product_category_id+IcodeSplitup.child_part_numbers["from_in_category"],
		icode__lte=product_category_id+IcodeSplitup.child_part_numbers["to_in_category"]
	).order_by("icode")


def get_child_part_numbers_of_pn(part_number = None, part_number_id = None): # get child part numbers by part number
	if part_number:
		part_number_id = part_number.icode
	part_number_id = int(part_number_id)
	return Icodes.objects.filter(
		icode__in=PnCpnMapping.objects.filter(part_number_i_id=part_number_id).values_list("child_part_number_i").distinct()
	).order_by("icode")


def get_child_part_numbers_of_pns(part_number_list = None, part_number_id_list = None): # get child part numbers by part numbers
	part_number_list =  part_number_list or []
	part_number_id_list =  part_number_id_list or []
	if part_number_list:
		for part_number in part_number_list: 
			part_number_id_list.append(part_number.icode)
	for index_i,i in enumerate(part_number_id_list):
		part_number_id_list[index_i] = int(i)
	return Icodes.objects.filter(
		icode__in=PnCpnMapping.objects.filter(part_number_i_id__in=part_number_id_list).values_list("child_part_number_i").distinct()
	).order_by("icode")


def get_part_status():
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.part_status['from'], icode__lte=IcodeSplitup.part_status['to'])).order_by("icode")


def get_part_status_rejection_and_rework():
	return Icodes.objects.filter(icode__in=[Others.rejected_part.icode, Others.rework_in_progress.icode]).order_by("icode")


def get_rejection_reasons(product_category = None, product_category_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	return Icodes.objects.filter(
		icode__gte=product_category_id+IcodeSplitup.rejection_reasons["from_in_category"],
		icode__lte=product_category_id+IcodeSplitup.rejection_reasons["to_in_category"]
	).order_by("icode")


def get_four_m_points():
	return Icodes.objects.filter(
		icode__gte=IcodeSplitup.four_m_ponits["from"],
		icode__lte=IcodeSplitup.four_m_ponits["to"]
	).order_by("icode")


def get_qa_patrol_checksheets_of_pl(production_line = None, production_line_id = None, alive_flag = None): # get quality patrol checksheets by production line
	if production_line:
		production_line_id=production_line.icode
	production_line_id = int(production_line_id)
	if not alive_flag is None:
		return PatrolCheckSheets.objects.filter(production_line_i_id=production_line_id, alive_flag=alive_flag).order_by("part_number_i", "cs_version")
	else:
		return PatrolCheckSheets.objects.filter(production_line_i_id=production_line_id).order_by("part_number_i", "cs_version")
	
	
def get_qa_patrol_checksheets_of_pns(part_number_list = None, part_number_id_list = None, alive_flag = None): # get quality patrol checksheets by part numbers
	part_number_list =  part_number_list or []
	part_number_id_list =  part_number_id_list or []
	if part_number_list:
		for part_number in part_number_list: 
			part_number_id_list.append(part_number.icode)
	for index_i,i in enumerate(part_number_id_list):
		part_number_id_list[index_i] = int(i)
	if not alive_flag is None:
		return PatrolCheckSheets.objects.filter(part_number_i_id__in=part_number_id_list, alive_flag=alive_flag).order_by("part_number_i", "cs_version")
	else:
		return PatrolCheckSheets.objects.filter(part_number_i_id__in=part_number_id_list).order_by("part_number_i", "cs_version")


def get_tools(product_category = None, product_category_id = None, tool_type = None, tool_type_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	if tool_type:
		tool_type_id = tool_type.icode
	if tool_type_id:
		tool_type_id = int(tool_type_id)
		if tool_type_id == Others.tool_tools.icode:
			return Icodes.objects.filter(
				icode__gte=product_category_id+IcodeSplitup.tool_tools["from_in_category"],
				icode__lte=product_category_id+IcodeSplitup.tool_tools["to_in_category"]
			).order_by("icode")
		else:
			return Icodes.objects.filter(
				icode__gte=product_category_id+IcodeSplitup.tool_fixtures["from_in_category"],
				icode__lte=product_category_id+IcodeSplitup.tool_fixtures["to_in_category"]
			).order_by("icode")
	return Icodes.objects.filter(
		Q(icode__gte=product_category_id+IcodeSplitup.tool_tools["from_in_category"], icode__lte=product_category_id+IcodeSplitup.tool_tools["to_in_category"]) |
		Q(icode__gte=product_category_id+IcodeSplitup.tool_fixtures["from_in_category"], icode__lte=product_category_id+IcodeSplitup.tool_fixtures["to_in_category"])
	).order_by("icode")


def get_tools_of_tpss(product_category = None, product_category_id = None, tool_type = None, tool_type_id = None): # get tools of tps mappings
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	if tool_type:
		tool_type_id = tool_type.icode 
	tool_type_id = int(tool_type_id)
	if tool_type_id == Others.tool_tools.icode:
		return Icodes.objects.filter(
			icode__in = TPsMapping.objects.filter(
				tool_i_id__gte=product_category_id+IcodeSplitup.tool_tools["from_in_category"],
				tool_i_id__lte=product_category_id+IcodeSplitup.tool_tools["to_in_category"]
			).values_list("tool_i_id").distinct()
		).order_by("icode")
	return Icodes.objects.filter(
		icode__in = TPsMapping.objects.filter(
			tool_i_id__gte=product_category_id+IcodeSplitup.tool_fixtures["from_in_category"],
			tool_i_id__lte=product_category_id+IcodeSplitup.tool_fixtures["to_in_category"]
		).values_list("tool_i_id").distinct()
	).order_by("icode")


def get_tools_of_ps(production_station = None, production_station_id = None, tool_type = None, tool_type_id = None): # get tools of production station
	if production_station:
		production_station_id=production_station.icode
	production_station_id = int(production_station_id) 
	if tool_type:
		tool_type_id = tool_type.icode
	if tool_type_id:
		tool_type_id = int(tool_type_id)
		product_category_id = get_product_category_by_item(item_id=production_station_id).icode
		if tool_type_id == Others.tool_tools.icode:
			return Icodes.objects.filter(
				icode__in = TPsMapping.objects.filter(
					tool_i_id__gte=product_category_id+IcodeSplitup.tool_tools["from_in_category"],
					tool_i_id__lte=product_category_id+IcodeSplitup.tool_tools["to_in_category"],
					production_station_i=production_station_id
				).values_list("tool_i_id").distinct()
			).order_by("icode")  
		else:
			return Icodes.objects.filter(
				icode__in = TPsMapping.objects.filter(
					tool_i_id__gte=product_category_id+IcodeSplitup.tool_fixtures["from_in_category"],
					tool_i_id__lte=product_category_id+IcodeSplitup.tool_fixtures["to_in_category"],
					production_station_i=production_station_id
				).values_list("tool_i_id").distinct()
			).order_by("icode")
	else:
		return Icodes.objects.filter(
			icode__in = TPsMapping.objects.filter(
				production_station_i=production_station_id
			).values_list("tool_i_id").distinct()
		).order_by("icode")


def get_poka_yokes(product_category = None, product_category_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	return Icodes.objects.filter(
		icode__gte=product_category_id+IcodeSplitup.poka_yokes["from_in_category"], 
		icode__lte=product_category_id+IcodeSplitup.poka_yokes["to_in_category"]
	).order_by("icode")


def get_pys_of_ps(production_station = None, production_station_id = None): # get pokayokes of production station
	if production_station:
		production_station_id=production_station.icode
	production_station_id = int(production_station_id) 	
	product_category_id = get_product_category_by_item(item_id=production_station_id).icode	
	return Icodes.objects.filter(
		icode__in = PyPsMapping.objects.filter(
			poka_yoke_i_id__gte=product_category_id+IcodeSplitup.poka_yokes["from_in_category"],
			poka_yoke_i_id__lte=product_category_id+IcodeSplitup.poka_yokes["to_in_category"],
			production_station_i=production_station_id
		).values_list("poka_yoke_i_id").distinct()
	).order_by("icode")  


def get_pyps_maps_of_pc(product_category = None, product_category_id = None):
	if product_category:
		product_category_id = product_category.icode
	product_category_id = int(product_category_id)
	return PyPsMapping.objects.filter(
		poka_yoke_i__in=get_poka_yokes(product_category_id=product_category_id) 
	)


def get_oee_events(dept_i = None, dept_id =None):
	if dept_i or dept_id:
		if dept_i:
			dept_id = dept_i.icode
		dept_id = int(dept_id)
		return Icodes.objects.filter(
			icode__in = OeDMapping.objects.filter(dept_i_id=dept_id)
		).order_by("icode")
	return Icodes.objects.filter(Q(icode__gte=IcodeSplitup.oee_events['from'], icode__lte=IcodeSplitup.oee_events['to'])).order_by("icode")


def get_ct_of_pn_on_pl(part_number=None, part_number_id=None, production_line = None, production_line_id = None,): # get cycle time pf part number on production line
	if part_number is None and part_number_id is None:
		if production_line:
			production_line_id = production_line.icode
		production_line_id = int(production_line_id)
		return get_icode_object(production_line_id).opls_pl.default_ct
	else:
		if part_number:
			part_number_id = part_number.icode
		if production_line:
			production_line_id = production_line.icode
		part_number_id = int(part_number_id)
		production_line_id = int(production_line_id)
		pnprl_data = PnPrlCtData.objects.filter(part_number_i_id=part_number, production_line_i_id=production_line_id)
		if pnprl_data.exists():
			return pnprl_data.first().cycle_time
		else:
			return get_icode_object(production_line_id).opls_pl.default_ct


def get_hmi_production_interrupt_msgs():
	return Icodes.objects.filter(icode__gte=IcodeSplitup.hmi_production_interrupt_msgs['from'], icode__lte=IcodeSplitup.hmi_production_interrupt_msgs['to']).order_by("icode")


def convert_float_with_int_possibility(float_value, ndigits=0): # it will round float to given number of digits and return int if rounded value is integer otherwise it will return float
	float_value = float(round(float_value, ndigits))
	if float_value.is_integer():
		return int(float_value)
	return float_value


def create_product_category(product_category_name):
	max_code = Icodes.objects.filter(
		icode__gte=IcodeSplitup.product_category["from"],
		icode=F('icode')-((F('icode')-IcodeSplitup.product_category["from"])%IcodeSplitup.product_category['period'])
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code + IcodeSplitup.product_category["period"]
	else:
		icode = IcodeSplitup.product_category["from"]
	Icodes.objects.create(icode=icode, name=product_category_name)


def create_technology(product_category, technology_name):
	max_code = Icodes.objects.filter(
		icode__gte=product_category.icode+IcodeSplitup.product_technologies["from_in_category"],
		icode__lte=product_category.icode+IcodeSplitup.product_technologies["to_in_category"]
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code+1
	else:
		icode = product_category.icode+IcodeSplitup.product_technologies["from_in_category"]
	Icodes.objects.create(icode=icode, name=technology_name)


def create_production_line(product_category, production_line_name):
	max_code = Icodes.objects.filter(
		icode__gte=product_category.icode+IcodeSplitup.production_lines["from_in_category"],
		icode__lte=product_category.icode+IcodeSplitup.production_lines["to_in_category"],
		icode=F('icode')-F('icode')%IcodeSplitup.production_lines['period_in_category']
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code + IcodeSplitup.production_lines["period_in_category"]
	else:
		icode = product_category.icode+IcodeSplitup.production_lines["from_in_category"]
	Icodes.objects.create(icode=icode, name=production_line_name)


def create_production_station(product_category, production_line, production_station_name):
	max_code = Icodes.objects.filter(
		icode__gt=production_line.icode ,
		icode__lt=production_line.icode + IcodeSplitup.production_lines['period_in_category']
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code + 1
	else:
		icode = production_line.icode + 1
	Icodes.objects.create(icode=icode, name=production_station_name)


def create_model(product_category, model_name):
	max_code = Icodes.objects.filter(
		icode__gte=product_category.icode+IcodeSplitup.product_models["from_in_category"],
		icode__lte=product_category.icode+IcodeSplitup.product_models["to_in_category"]
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code+1
	else:
		icode = product_category.icode+IcodeSplitup.product_models["from_in_category"]
	Icodes.objects.create(icode=icode, name=model_name)


def create_part_number(product_category, part_number_name, part_number_desc):
	max_code = Icodes.objects.filter(
		icode__gte=product_category.icode+IcodeSplitup.part_numbers["from_in_category"],
		icode__lte=product_category.icode+IcodeSplitup.part_numbers["to_in_category"]
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code+1
	else:
		icode = product_category.icode+IcodeSplitup.part_numbers["from_in_category"]
	Icodes.objects.create(icode=icode, name=part_number_name, description=part_number_desc)   


def create_child_part_number(product_category, child_part_number_name, child_part_number_desc):
	max_code = Icodes.objects.filter(
		icode__gte=product_category.icode+IcodeSplitup.child_part_numbers["from_in_category"],
		icode__lte=product_category.icode+IcodeSplitup.child_part_numbers["to_in_category"]
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code+1
	else:
		icode = product_category.icode+IcodeSplitup.child_part_numbers["from_in_category"]
	Icodes.objects.create(icode=icode, name=child_part_number_name, description=child_part_number_desc)


def create_rejection_reason(product_category, rejection_reason_name):
	max_code = Icodes.objects.filter(
		icode__gte=product_category.icode+IcodeSplitup.rejection_reasons["from_in_category"],
		icode__lte=product_category.icode+IcodeSplitup.rejection_reasons["to_in_category"]
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code+1
	else:
		icode = product_category.icode+IcodeSplitup.rejection_reasons["from_in_category"]
	Icodes.objects.create(icode=icode, name=rejection_reason_name)


def create_tool(product_category, tool_type, tool_name):
	if tool_type == Others.tool_tools:
		max_code = Icodes.objects.filter(
			icode__gte=product_category.icode+IcodeSplitup.tool_tools["from_in_category"],
			icode__lte=product_category.icode+IcodeSplitup.tool_tools["to_in_category"]
		).aggregate(Max("icode"))["icode__max"]
		if max_code:
			icode = max_code+1
		else:
			icode = product_category.icode+IcodeSplitup.tool_tools["from_in_category"]
	elif tool_type == Others.tool_fixtures:
		max_code = Icodes.objects.filter(
			icode__gte=product_category.icode+IcodeSplitup.tool_fixtures["from_in_category"],
			icode__lte=product_category.icode+IcodeSplitup.tool_fixtures["to_in_category"]
		).aggregate(Max("icode"))["icode__max"]
		if max_code:
			icode = max_code+1
		else:
			icode = product_category.icode+IcodeSplitup.tool_fixtures["from_in_category"]
	Icodes.objects.create(icode=icode, name=tool_name)


def create_poka_yoke(product_category, poka_yoke_name):
	max_code = Icodes.objects.filter(
		icode__gte=product_category.icode+IcodeSplitup.poka_yokes["from_in_category"],
		icode__lte=product_category.icode+IcodeSplitup.poka_yokes["to_in_category"]
	).aggregate(Max("icode"))["icode__max"]
	if max_code:
		icode = max_code+1
	else:
		icode = product_category.icode+IcodeSplitup.poka_yokes["from_in_category"]
	Icodes.objects.create(icode=icode, name=poka_yoke_name)


class ShiftA:
	def __init__(self) -> None:
		self.shift = get_icode_object(icode=IcodeSplitup.icode_shiftA)
		self.icode = self.shift.icode
		self.name = self.shift.name
		self.ps = get_icode_object(icode=IcodeSplitup.icode_shiftC) # previous shift
		self.ns = get_icode_object(icode=IcodeSplitup.icode_shiftB) # next shift
		self.past_shift_list = []
		self.future_shift_list = [self.ns, self.ps]
		self.day_delta = 0
		self.bg_color = "#EB984E"
		self.txt_color = "#FFFFFF"
		self.params_avl = None
		# print("class", __class__.__name__, "initialized")
		self.initialize_shift_params()

	def initialize_shift_params(self):
		if self.name != na_str:
			self.start_dt = datetime.datetime.strptime(self.shift.description, format_of_shift_time)
			self.start_time = self.start_dt.time()
			self.ns_start_dt = datetime.datetime.strptime(self.ns.description, format_of_shift_time)
			self.ns_start_time = self.ns_start_dt.time()
			self.duration_time = self.ns_start_dt - self.start_dt + datetime.timedelta(days=self.day_delta)
			self.params_avl = True
	
	def start_date_time(self, date):
		return datetime.datetime.combine(date, self.start_time)

	def ns_start_date_time(self, date):
		return datetime.datetime.combine(date + datetime.timedelta(days=self.day_delta), self.ns_start_time)

	def __str__(self):
		return self.name
	

class ShiftB(ShiftA):
	def __init__(self) -> None:
		super().__init__()
		self.shift = get_icode_object(icode=IcodeSplitup.icode_shiftB)
		self.icode = self.shift.icode
		self.name = self.shift.name
		self.ps = get_icode_object(icode=IcodeSplitup.icode_shiftA) # previous shift
		self.ns = get_icode_object(icode=IcodeSplitup.icode_shiftC) # next shift
		self.past_shift_list.append(self.ps)
		self.future_shift_list.remove(self.shift)
		self.day_delta = 0
		self.bg_color = "#58D68D"
		self.txt_color = "#FFFFFF"
		self.params_avl = None
		# print("class", __class__.__name__, "initialized")
		self.initialize_shift_params()


class ShiftC(ShiftB):
	def __init__(self) -> None:
		super().__init__()
		self.shift = get_icode_object(icode=IcodeSplitup.icode_shiftC)
		self.icode = self.shift.icode
		self.name = self.shift.name
		self.ps = get_icode_object(icode=IcodeSplitup.icode_shiftB) # previous shift
		self.ns = get_icode_object(icode=IcodeSplitup.icode_shiftA) # next shift
		self.past_shift_list.append(self.ps)
		self.future_shift_list.remove(self.shift)
		self.day_delta = 1
		self.bg_color = "#5DADE2"
		self.txt_color = "#FFFFFF"
		self.params_avl = None
		# print("class", __class__.__name__, "initialized")
		self.initialize_shift_params()


class OEEShiftA(ShiftA):
	def __init__(self) -> None:
		super().__init__()
		self.no_of_tb = 2 # no of tea breaks for the shift
		self.no_of_fb = 1 # no of food breaks for the shift
		if self.params_avl:
			self.generate_oee_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_generate_shift_oee_in_min)).time()
			self.oee_report_mail_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_oee_report_mail_in_min)).time()
			self.dt_report_mail_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_dt_report_mail_in_min)).time()


class OEEShiftB(ShiftB):
	def __init__(self) -> None:
		super().__init__()
		self.no_of_tb = 2 # no of tea breaks for the shift
		self.no_of_fb = 1 # no of food breaks for the shift
		if self.params_avl:
			self.generate_oee_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_generate_shift_oee_in_min)).time()
			self.oee_report_mail_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_oee_report_mail_in_min)).time()
			self.dt_report_mail_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_dt_report_mail_in_min)).time()


class OEEShiftC(ShiftC):
	def __init__(self) -> None:
		super().__init__()
		self.no_of_tb = 2 # no of tea breaks for the shift
		self.no_of_fb = 1 # no of food breaks for the shift
		if self.params_avl:
			self.generate_oee_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_generate_shift_oee_in_min)).time()
			self.oee_report_mail_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_oee_report_mail_in_min)).time()
			self.dt_report_mail_time = (self.ns_start_dt + datetime.timedelta(minutes=Others.a007_wait_for_dt_report_mail_in_min)).time()
	

class Shifts:
	ShiftA = ShiftA()
	ShiftB = ShiftB()
	ShiftC = ShiftC()


class Genders:
	Male = get_icode_object(icode=16)
	Female = get_icode_object(icode=17)

	
class PlantLocations:
	SP_Koil = get_icode_object(icode=101)
	Trichy = get_icode_object(icode=102)
	Singadivakkam = get_icode_object(icode=103)
	All_plant_locations = "all_depts"


class Depts:
	PLE = get_icode_object(icode=121)
	ME = get_icode_object(icode=122)
	MFG = get_icode_object(icode=123)
	Inprocess_QA = get_icode_object(icode=124)
	Incoimg_QA = get_icode_object(icode=125)
	Development_team = get_icode_object(icode=126)
	Engg = get_icode_object(icode=127)
	MKT = get_icode_object(icode=128)
	HR = get_icode_object(icode=129)
	MMD = get_icode_object(icode=130)
	OM = get_icode_object(icode=131)
	LM = get_icode_object(icode=132)
	TQM = get_icode_object(icode=133)
	TEI = get_icode_object(icode=134)
	Business_administration = get_icode_object(icode=140)
	All_depts = "all_depts"


class Designations:
	Interns_or_Trainees = get_icode_object(icode=141)
	Craftsman = get_icode_object(icode=142)
	Deputy_Engineer_or_Executive = get_icode_object(icode=143)
	Engineer_or_Executive = get_icode_object(icode=144)
	Senior_Engineer_or_Executive = get_icode_object(icode=145)
	Assistant_Manager = get_icode_object(icode=146)
	Deputy_Manager = get_icode_object(icode=147)
	Manager = get_icode_object(icode=148)
	Senior_Manager = get_icode_object(icode=149)
	Assistant_GM = get_icode_object(icode=150)
	Deputy_GM = get_icode_object(icode=151)
	General_Manager = get_icode_object(icode=152)
	Assoicite_VP = get_icode_object(icode=153)
	Vice_President = get_icode_object(icode=154)
	Senior_VP = get_icode_object(icode=155)
	President = get_icode_object(icode=156)
	All_designations = "all_designations"



class Apps:
	# app keys length should be less than or equal to 10
	class A000XylemMaster:
		obj = get_icode_object(icode=300)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['Q9BR1xpWWF', 'prFJqjdPhS', 'DUGmB14HYQ', 'zQzd7sdDis', '6MR9O3y8Cc', '4mHjj5mO10', '6JfXcKdpmx', 'SWhUHW5eEm', 'QfZwjqhRBQ', 'ANefky3nDw']
	
	class A001QAReportAndReprocess:
		obj = get_icode_object(icode=301)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['uFSICjDZlJ', 'REttxf63mu', 'LY2Ou4ogxo', 'TuVMeyHA5G', 'XL6MIWhUoG', 'q0nQwNWKvm', '4pyAoomGdz', 'BZsbijX7EK', 'DOM9BQc5m3', 'iqGku8ya9m']
		line_key_list = ["line_name_on_web_page","stns"]
		stn_key_list = [
			"stn_name_on_web_page",
			"sql_instance_name",
			"user_name",
			"password",
			"database_name",
			"table_name",
			"serialno_col_name",
			"result_col_name",
			"datetime_col_name",
			"sort_by_col_name",
			"remarks_col_name"
		]
		report_wt = 1
		reprocess_wt = 2
		cache_key_of_reprocess_eligible_dict = 'reprocess_eligible_dict'
		cache_key_of_server_connection_dict = 'server_connection_dict'
		cache_key_of_master_dict = 'master_dict'
    
	class A002SBSRejectionEntryAndRework:
		obj = get_icode_object(icode=302)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['LNXqKxoF2h', '7yR5c7Pv0M', 'QOHKSm6NBt', 'zcTUVjVjDv', 'A5yNLhn1aa', 'KPlulAmTcs', 'PXFYsEWEuG', '5eP619fxyB', 'MC2aK3g3TD', 's9QoU12dRL']
	
	class A003SmartAlerts:
		obj = get_icode_object(icode=303)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['mkQ5rj7VIz', 'UtiOUX6kCQ', '1otiy1HTnu', 'mw1ibWS5Js', 'Ycw36nP474', 'PRrO9miwIO', 'lGiBv3VD85', 'o9gNIVvZwl', '8C4adKYxI8', 'Cr0nENt8wE']
	
	class A004ToolsManagementSystem:
		obj = get_icode_object(icode=304)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['NPNbNdF7UJ', '3kLH9ztVAX', 'VnNwUyaHL6', '9ZSxynBiw1', 'oxTnmrXqDa', 'S1J3mskdEg', 'PwK4b4psze', 'WM7vUhXmzY', 'XnERVhw7MP', '18bX89E1uE']
	
	class A005QAPatrolCheck:
		obj = get_icode_object(icode=305)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['ccPE0zmx2Y', '2ZMbHDwMnX', 'zG6mAGew6c', 'Tsu0lCJCNK', 'N2mNh6Jkbr', 'xGImBuy0eR', 'l4qKYLb2df', 'ePON7NqoBk', '1mNY31lOIL', 'MPZKMl2Ius']
	
	class A0064MDigitalization:
		obj = get_icode_object(icode=306)
		icode = obj.icode
		name = obj.name
		description = obj.description
		min_approver_designation = Designations.Assistant_Manager
		bw_logger_name = f'{description}_bw'
		appr_design_of_four_m = Designations.Assistant_Manager
		xrh_app_queue = queue.Queue()
		app_key_list = ['GyZF1lE1pP', 'dcVPCto7zK', 'ukvnHekgZ5', 'yG90rqab32', 'Brx2QF7F13', 'VfFPwxCXq9', 'sNwAwyjh4a', '9ulCWDSvfU', 'NalpFcKJQ9', 'FNAMowRCRL']
	
	class A007OEEMonitoring:
		obj = get_icode_object(icode=307)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		cache_key_of_oee_dict = 'oee_dict'
		cache_key_of_oee_dashboard_dict = 'oee_dashboard_dict'
		xrh_app_queue = queue.Queue()
		app_key_list = ['gkXdawR5G6', 'ujb7fvLKsw', 'aJT4mwH317', '88hm7srQgN', 'koCPxpGeJG', 'uw9147UVm6', 'bpN854mdoy', 'yzt2R4vZuG', 'tv6BY3IpJH', 'TAXdagIffC']
	
	class A008HomeSchemer:
		obj = get_icode_object(icode=308)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['Tj5iFNlvaV', '7T7cVwhJeu', 'swmjuAUvvN', 'CUDGENr082', 'ocCUG3vlSo', 'Ysg2ecHaoe', 'JaN2da46Y5', 'MCuy8emcw5', 'vVfTppXs7c', '6qLmlZH6Wd']
	
	class A009BuildingManagementSystem:
		obj = get_icode_object(icode=309)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['M4pnHIftEv', 'mXH9nBUHdI', 'a5yxwZJgwe', 'dvARqOjW6H', '3sEixSZWZ3', 'OadxNz4yba', 'gGRRbgVQJh', 'gQGnWqVv7Z', 'tSXOaCozYb', '37taR3OWxO']

	class A010PokaYokeMonitoring:
		obj = get_icode_object(icode=310)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['Mq7vuD46lv', 'JkvErWvht1', '0dFW3NndMp', 's0Z4CdopOQ', '8XjZLzxGZS', 'r49IN48xPa', '31vU7j7mdK', 'QhnJo5nccN', 'O8UHabY0Sy', 'cuvT0LNUFs']
		inspec_ok = True
		inspec_nok = False
		inspec_waiting = None
		inspec_missed = None
	
	class A011Workflows:
		obj = get_icode_object(icode=311)
		icode = obj.icode
		name = obj.name
		description = obj.description
		bw_logger_name = f'{description}_bw'
		xrh_app_queue = queue.Queue()
		app_key_list = ['Mq7vuD46lv', 'JkvErWvht1', '0dFW3NndMp', 's0Z4CdopOQ', '8XjZLzxGZS', 'r49IN48xPa', '31vU7j7mdK', 'QhnJo5nccN', 'O8UHabY0Sy', 'cuvT0LNUFs']


class ProductCategory:
	seat_belt = get_icode_object(icode=500000)
	buckle = get_icode_object(icode=1000000)


class Mails:
	a000_local_projects_ifs1_bb_pin_press_vision_report_mail = get_icode_object(icode=400)
	a003_web_pulling_ng_alert_mail = get_icode_object(icode=401)
	a004_low_tool_life_alert_mail = get_icode_object(icode=402)
	a004_tool_life_boost_mail = get_icode_object(icode=403)
	a007_oee_day_report_mail = get_icode_object(icode=404)
	a007_downtime_day_report_mail = get_icode_object(icode=405)
	a007_major_losses_of_day_mail = get_icode_object(icode=406)
	a007_part_number_day_report_mail = get_icode_object(icode=407)
	a007_production_plan_vs_actual_mail = get_icode_object(icode=408)
	a009_water_consumption_report_p1_mail = get_icode_object(icode=409)
	a010_poke_yoke_status_update_mail = get_icode_object(icode=410)
	a003_cop_pn_alert_mail = get_icode_object(icode=411)
	a007_production_day_summary_mail = get_icode_object(icode=412)
	a003_friction_welding_ng_alert_mail = get_icode_object(icode=413)


class ApprovalModes:
	xylem_local_site = get_icode_object(icode=41)
	xylem_remote_site = get_icode_object(icode=42)
	auto_response = get_icode_object(icode=43)


class Others:
	rejected_part = get_icode_object(icode=2)
	process_in_progress = get_icode_object(icode=3)
	rework_in_progress = get_icode_object(icode=4)
	rework_completed = get_icode_object(icode=5)
	yes_option = get_icode_object(icode=8)
	no_option = get_icode_object(icode=9)
	active_checksheets_option = get_icode_object(icode=36)
	deactivated_checksheets_option = get_icode_object(icode=37)
	all_checksheets_option = get_icode_object(icode=38)
	active_workflows_option = get_icode_object(icode=46)
	deactivated_workflows_option = get_icode_object(icode=47)
	holded_workflows_option = get_icode_object(icode=48)
	all_workflows_option = get_icode_object(icode=49)
	tool_tools = get_icode_object(icode=23)
	tool_fixtures = get_icode_object(icode=24)
	tea_break_duration = get_icode_object(icode=14)
	food_break_duration = get_icode_object(icode=15)
	partnumbers_with_drawings = get_icode_object(icode=56)
	Partnumbers_without_drawings = get_icode_object(icode=57)
	where_id_obj_spr8_bb_friction_welding_machine = get_icode_object(icode=601311)
	day_bg_color = "#03293B"
	day_txt_color = "#FFFFFF"
	a007_wait_for_generate_shift_oee_in_min = 1
	a007_wait_for_oee_report_mail_in_min = 5
	a007_wait_for_dt_report_mail_in_min = 30
	a007_wait_for_ml_report_mail_in_min = 30
	a007_wait_for_pn_report_mail_in_min = 5
	a007_wait_for_plan_vs_actual_report_mail_in_min = 5
	a009_income_flow_meters_list = [get_icode_object(icode=161)]
	a009_s1_cosumption_flow_meters_list = [get_icode_object(icode=162), get_icode_object(icode=164)]
	a009_s2_cosumption_flow_meters_list = [get_icode_object(icode=163), get_icode_object(icode=165)]
	a009_s3_cosumption_flow_meters_list = [] # [get_icode_object(icode=166)] # do change in get_flow_meters also


class OEE:
	no_plan = get_icode_object(icode=10066)
	tea_break = get_icode_object(icode=10069)
	food_break = get_icode_object(icode=10070)
	preventive_maintenace_me = get_icode_object(icode=10063)
	preventive_maintenace_ple = get_icode_object(icode=10067)
	tea_break_excess = get_icode_object(icode=10153)
	food_break_excess = get_icode_object(icode=10154)
	ongoing_idletime = get_icode_object(icode=10145)
	uncaptured_event = get_icode_object(icode=10148)
	shift_windup = get_icode_object(icode=10151)
	server_restart_event = get_icode_object(icode=10075)

	depts_list = [Depts.PLE, Depts.ME, Depts.MMD, Depts.HR, Depts.MFG, Depts.Inprocess_QA]
	dashboard_color_code_dict = {
		"plan_time": { 
			"name": "Plan Time",
			"bg_color": bs_primary_color,
			"txt_color": "#FFFFFF",
		},
		"no_plan": { 
			"name": "No Plan",
			"bg_color": bs_secondary_color,
			"txt_color": "#FFFFFF",
		},
		"no_loss": { 
			"name": "No Loss",
			"bg_color": "#00FF00",
			"txt_color": "#000000",
		},
		"og_it": { 
			"name": "Ongoing Idle",
			"bg_color": loss_bg_color,
			"txt_color": "#FFFFFF",
		},
		f"dept_loss_{Depts.PLE.icode}": { 
			"name": Depts.PLE.description,
			"bg_color": "#FF6400",
			"txt_color": "#FFFFFF",
		},
		f"dept_loss_{Depts.ME.icode}": { 
			"name": Depts.ME.description,
			"bg_color": "#808000",
			"txt_color": "#FFFFFF",
		},
		f"dept_loss_{Depts.MMD.icode}": { 
			"name": Depts.MMD.description,
			"bg_color": "#0000B3",
			"txt_color": "#FFFFFF",
		},
		f"dept_loss_{Depts.HR.icode}": { 
			"name": Depts.HR.description,
			"bg_color": "#FF00FF",
			"txt_color": "#FFFFFF",
		},
		f"dept_loss_{Depts.MFG.icode}": { 
			"name": Depts.MFG.description,
			"bg_color": "#A200FF",
			"txt_color": "#FFFFFF",
		},
		f"dept_loss_{Depts.Inprocess_QA.icode}": { 
			"name": Depts.Inprocess_QA.description,
			"bg_color": "#C5C830",
			"txt_color": "#FFFFFF",
		},
	}
	ShiftA = OEEShiftA()
	ShiftB = OEEShiftB()
	ShiftC = OEEShiftC()

	if ShiftA.params_avl:
		day_ml_report_mail_time = (ShiftA.start_dt + datetime.timedelta(minutes=Others.a007_wait_for_ml_report_mail_in_min)).time()
		day_pn_report_mail_time = (ShiftA.start_dt + datetime.timedelta(minutes=Others.a007_wait_for_pn_report_mail_in_min)).time()
		day_plan_vs_actual_report_mail_time = (ShiftA.start_dt + datetime.timedelta(minutes=Others.a007_wait_for_plan_vs_actual_report_mail_in_min)).time()
		T = list(map(int,Others.tea_break_duration.description.strip().split(":")))
		F = list(map(int,Others.food_break_duration.description.strip().split(":")))
		tea_break_point_time = datetime.datetime.strptime(Others.tea_break_duration.description, format_of_break_time).time()
		food_break_point_time = datetime.datetime.strptime(Others.food_break_duration.description, format_of_break_time).time()
		tea_break_time_duration_td = datetime.timedelta(hours=tea_break_point_time.hour, minutes=tea_break_point_time.minute, seconds=tea_break_point_time.second)
		food_break_duration_td = datetime.timedelta(hours=food_break_point_time.hour, minutes=food_break_point_time.minute, seconds=food_break_point_time.second)
	planned_oee_events = [tea_break, food_break, no_plan, preventive_maintenace_me, preventive_maintenace_ple]


def get_all_operators():
	return UserProfile.objects.filter(is_active=True).filter(Q(designation_i=Designations.Interns_or_Trainees) | Q(designation_i=Designations.Craftsman))


def get_shift(dt):
	t = dt.time()
	if Shifts.ShiftA.start_time <= t < Shifts.ShiftB.start_time:
		return Shifts.ShiftA
	elif Shifts.ShiftB.start_time <= t < Shifts.ShiftC.start_time:
		return Shifts.ShiftB
	else:
		return Shifts.ShiftC


def get_shift_obj(shift = None, shift_id = None): # get shift object by shift 
	if shift:
		shift_id = shift.icode
	shift_id = int(shift_id)
	if shift_id == Shifts.ShiftA.icode:
		return Shifts.ShiftA
	elif shift_id == Shifts.ShiftB.icode:
		return Shifts.ShiftB
	elif shift_id == Shifts.ShiftC.icode:
		return Shifts.ShiftC


def get_oee_shift(dt):
	t = dt.time()
	if Shifts.ShiftA.start_time <= t < Shifts.ShiftB.start_time:
		return OEE.ShiftA
	elif Shifts.ShiftB.start_time <= t < Shifts.ShiftC.start_time:
		return OEE.ShiftB
	else:
		return OEE.ShiftC


def get_custom_shift_date(dt):
	if dt.time() < Shifts.ShiftA.start_time :
		return (dt - datetime.timedelta(days=Shifts.ShiftC.day_delta)).date()
	return dt.date()


def get_start_of_the_day(dt):
	return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_standard_str_format_of_dt_or_d(dt=None, d=None):
	if dt:
		return dt.strftime("%B %d, %Y, %I:%M %p").replace("AM", "a.m.").replace("PM", "p.m.")
	else:
		return d.strftime("%B %d, %Y")


def get_bg_txt_color_of_percent(percent):
	if percent >= percent_high_start:
		return percent_high_bg_color, percent_high_txt_color
	elif percent >= percent_mid_start:
		return percent_mid_bg_color, percent_mid_txt_color
	else:
		return percent_low_bg_color, percent_low_txt_color
	

def run_as_thread(job_func, args=None):
	th = threading.Thread(target=job_func, args=args or (), daemon=True)
	th.start()
	return th


def send_mail(app_name, subject, to_list=None, cc_list=None, bcc_list=None, text_content=None, html_content=None, attachments_path_list=None,run_in_thread=False,):
    def send_mail_thread():
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content or "",
            from_email= EMAIL_HOST_USER,
            to=to_list or [],
            cc=cc_list or [],
            bcc=bcc_list or [],
        )      
        if html_content:
            msg.attach_alternative(html_content, "text/html")
        attached_files = []

        # SAFE ATTACHMENT METHOD
        if attachments_path_list:
            for file_path in attachments_path_list:
                try:
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        msg.attach_file(file_path)
                        attached_files.append(file_path)                    
                except Exception as e:
                    mail_handler_logger.error(f"{app_name}: Failed to attach {file_path}. Error: {e}", exc_info=True)
        retry_count = 0
        sent = False
        while retry_count < mail_max_retry_count:
            try:
                msg.send()
                sent = True
                mail_handler_logger.info( f"{app_name}: '{subject}' sent successfully to {to_list}")               
                time.sleep(2)# Delay BEFORE deleting attachments (CRITICAL)
                for file_path in attached_files:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        mail_handler_logger.warning(f"{app_name}: Failed to delete {file_path}. Error: {e}")
                break
            except Exception as e:
                retry_count += 1
                mail_handler_logger.warning(f"{app_name}: Mail send failed (Attempt {retry_count}). Error: {e}")
                time.sleep(3)

        # SAVE ONLY IF ALL RETRIES FAILED
        if not sent:
            try:
                UnsentMails.objects.create(
                    subject=subject,
                    text_content=text_content,
                    html_content=html_content,
                    to_list=to_list,
                    cc_list=cc_list,
                    bcc_list=bcc_list,
                    attachments_path_list=attachments_path_list,
                )
                mail_handler_logger.error(
                    f"{app_name}: '{subject}' mail saved to UnsentMails after "
                    f"{mail_max_retry_count} failed attempts", exc_info=True
                )
            except Exception as e:				
                mail_handler_logger.error(f"{app_name}: Failed to save unsent mail '{subject}'. Error: {e}", exc_info=True)
    if run_in_thread:
        threading.Thread(target=send_mail_thread, daemon=True).start()
    else:
        send_mail_thread()


def get_xylem_manage_mail_footer_html():
	return mark_safe(f'''<hr> <div style="text-align: center; font-size: 10px;">
      <a href="{xylem_host_main_url}/manage_mails/">Manage Xylem Mails using PCs</a>|  
      <a href="{xylem_host_router_url}/manage_mails/">Manage Xylem Mails using Mobiles</a>
    </div>''')


def get_from_background_worker_api(url, **kwargs):
	if "method" in kwargs:
		method = kwargs.pop("method")
		if method == "POST":
			return requests.post(xylem_background_worker_host_name + url, **kwargs)
	return requests.get(xylem_background_worker_host_name + url, **kwargs)


an_xylem_master = Apps.A000XylemMaster.description
an_qa_report_and_reprocess = Apps.A001QAReportAndReprocess.description
an_sbs_rejection_entry_and_rework = Apps.A002SBSRejectionEntryAndRework.description
an_smart_alerts = Apps.A003SmartAlerts.description
an_tools_management_system = Apps.A004ToolsManagementSystem.description
an_qa_patrol_check = Apps.A005QAPatrolCheck.description
an_4m_digitalization = Apps.A0064MDigitalization.description
an_oee_monitoring = Apps.A007OEEMonitoring.description
an_home_schemer = Apps.A008HomeSchemer.description
an_building_management_system = Apps.A009BuildingManagementSystem.description
an_poka_yoke_monitoring = Apps.A010PokaYokeMonitoring.description
an_workflows = Apps.A011Workflows.description

scheduler_delay_in_milli_seconds = 3000
error_wait_in_milliseconds = 3000
scheduler_delay = scheduler_delay_in_milli_seconds/1000
error_wait = error_wait_in_milliseconds/1000
trigger_delay_for_maintanenece_alert_in_milliseconds = 20000
trigger_delay_for_maintanenece_alert = trigger_delay_for_maintanenece_alert_in_milliseconds/1000
chat_max_retry_count = 3 # Maximum 3
mail_max_retry_count = 5


# [Xylem Remote]  -- start 
app_key_split_indices_list = first_n_primes(len(Apps.A000XylemMaster.app_key_list[0]))


progress_level_key_dict = {
	1: ['osIHXODFC5', 'LQRsqqeEJv', 'ZaPGCrdhW6', '2id4wdGhO8', 'OhWJZW9wmK', 'yNSOkP0Yol', 'yg5KyqbL4q', 'zukkaqrBNB', 'p2CoTlT943', 'IdSXWsNe1t'],
	2: ['GQcUhPNdaR', 'HWTBOwmejy', '13hYE35J0K', 'b1vlpAaUPk', 'jkApLYx2C9', '52DBpQP8Zu', 'QeCaWxctqy', 'Ox7SLPTuip', 'whva7k1iGM', 'UJghHaGFgN'],
	3: ['iJ3v9qhTRg', 'C9ufTxsyoo', 'x5OwXgbZQ3', 'WohP8pV2rR', '4g3mF9PmVy', 'WmJK6Sg2uK', '9a1sRj64mY', 'sZTemGaOlX', 'aJvQ9FsaPG', 'dKohlkJB5H'],
	4: ['WNAcHMSoVA', 'Vy9xIMaKx4', 'hegc7VqePK', 'oegjBQKWs6', 'HC20vpfynR', 'YQQVzQ0Jsf', 'UZGTW3Ekd0', 'gmg1wSYNbQ', 'KBtfJYiK5I', 'ERYAz7muya'],
	5: ['iMvgJz68vl', 'SX2ncy0anV', 'rTo0JdS3Az', '1dS60gotWw', 'qlsyN8ZLWO', '1rnZ3NhGx8', 'Jf0mdbWCbk', 'oA3SRMGwjj', 'VUNzK99DlR', '7Ccdovdr8j'],
	6: ['bl7L2SAYCQ', 'kD2XIkLwL5', 'tXAn1jfl2e', 'YJsSUA42lt', 'egrTIGiFrD', '7ZDONKq8sm', 'kQpFsPAPNz', '666Oypnxc4', '4LGHizvdY6', 'sjL6ypxyC8'],
	7: ['Xh6luBIYUs', 'F1kjTABMjf', 've1XccP73d', 'OIECDX92a6', 'GqNxEZZh81', '3MZJnzSP5B', 'BA38kQLi8x', 'SrXDG1JB6o', '4YZcrkk53q', '0de69zskYz'], 
	8: ['1zq9FQW2jM', 'uMXXDjjkww', 'X3b7yqJeoN', 'mTTfAATY3n', 'NOlgfHjE56', 'n75t9oERM7', 'SHVMxSxQZD', 'r82WJjUt2C', 'YKXL0YYQfH', 'MECz1aQ9bm'],
	9: ['mZoS9pZWRj', 'Q1lZKL9zee', 'VKxk8I05tt', 'O0clAM2tKi', 'lnT82V9jsz', 'Hq5SEh6pZf', 'ZiOzRQfbva', '1uPtP4cQhm', 'rZpLHfwpy9', '7jbZNhCnwA'],
	10: ['3lRJuOVNRj', 'G3ZUHWdMmu', 'rqso0urEv4', '9sasw7tvf0', 'FqmsfFydoI', '4s2tFJNqIJ', 'a0vAAdBlQ0', 'IWNTmbm0r2', 'Q405drzCZS', 'NkTTOROiUn']
}


class XylemRemoteServices:
	# One session can approve one form at a time, likewisw only programmed
	class S000XylemRemoteMaster:
		name = "s000"	
		codes = ["ruyiytmkjgf", "Vhioknmkgt", "LhsoyPohfg", "L29opXUYwl", "IyrhDnGayh", "OuyshJhsay", "YloitBnjpo", "IpurhNmViut", "YoiytrjKi", "pOUJHFTyO"]
		response_timeout = 10

		class Progress:		
			xylem_login_validation = SimpleNamespace(code=1, desc="Validate Xylem User")

		class Validation:
			valid_xylem_user = SimpleNamespace(code=1, desc="Welcome! You have access to Xylems remote.")
			invalid_xylem_user = SimpleNamespace(code=2, desc="Access denied. You are not registered in Xylem.")
			ifs_approval_pending = SimpleNamespace(code=3, desc="Your approval is still pending with your IFS.")
			ifs_approval_denied = SimpleNamespace(code=4,desc="Your login request was rejected by IFS.")
			invalid_credentials = SimpleNamespace(code=5, desc="Please enter a valid username and password.")
			previous_validation_not_done = SimpleNamespace(code=6, desc="Previous Validation Not Done")
			invalid_request = SimpleNamespace(code=7, desc="Invalid Request")

		class UserResponse:
			approve = SimpleNamespace(code=1, desc="Ok")
			reject = SimpleNamespace(code=2, desc="Reject")

		def get_progress_description(code):
			for attr_name in dir(XylemRemoteServices.S000XylemRemoteMaster.Progress):
				attr = getattr(XylemRemoteServices.S000XylemRemoteMaster.Progress, attr_name)
				if isinstance(attr, SimpleNamespace) and attr.code == code:
					return attr.desc			
				
		def get_validation_description(code):
			for attr_name in dir(XylemRemoteServices.S000XylemRemoteMaster.Validation):
				attr = getattr(XylemRemoteServices.S000XylemRemoteMaster.Validation, attr_name)
				if isinstance(attr, SimpleNamespace) and attr.code == code:
					return attr.desc
				
	class S001XylemRemoteApproval:
		name = "s001"
		codes = ['nd3nPfag7X', 'ChCPrCTglk', 'u17BGW4IvY', 'L22opXoFwl', 'OsoXYzY55Y', '4WwVL8eM5e', '5ASsQxwzRU', 'AfiLV0mroZ', 'UsjrUF3hEK', 'pPDWY5wz1W']
		response_timeout = 10  # seconds

		class Progress:
			validate_form = SimpleNamespace(code=1, desc="Validate Form")
			validate_form_status = SimpleNamespace(code=2, desc="Validate Form Status")
			validate_user = SimpleNamespace(code=3, desc="Validate User")
			submit_response = SimpleNamespace(code=4, desc="Submit Response")
		
		class Validation:
			ok = SimpleNamespace(code=1, desc="Validation Ok")
			invalid_request = SimpleNamespace(code=2, desc="Invalid Request")
			previous_validation_not_done = SimpleNamespace(code=3, desc="Previous Validation Not Done")
			invalid_form = SimpleNamespace(code=4, desc="Invalid Form")
			already_approved_by_you = SimpleNamespace(code=5, desc="Already Approved by You")
			already_rejected_by_you = SimpleNamespace(code=6, desc="Already Rejected by You")
			already_approved_by_other = SimpleNamespace(code=7, desc="Already Approved by Other")
			already_rejected_by_other = SimpleNamespace(code=8, desc="Already Rejected by Other")
			invalid_user = SimpleNamespace(code=9, desc="Your criteria are not fulfilled for the approval")
			invalid_user_dept = SimpleNamespace(code=10, desc="Form not raised to the department belongs to you")
			already_approved_by_you_recently = SimpleNamespace(code=11, desc="Already Approved by You recently")
			already_approved_by_other_recently = SimpleNamespace(code=12, desc="Already Approved by Other recently")
			already_rejected_by_you_recently = SimpleNamespace(code=13, desc="Already Rejected by You recently")
			already_rejected_by_other_recently = SimpleNamespace(code=14, desc="Already Rejected by Other recently")
			valid_xylem_user = SimpleNamespace(code=15, desc="This person is a xylem User")
			invalid_xylem_user = SimpleNamespace(code=16, desc="This person is not a xylem User")
		
		class UserResponse:
			approve = SimpleNamespace(code=1, desc="Approve")
			reject = SimpleNamespace(code=2, desc="Reject")

		def get_progress_description(code):
			for attr_name in dir(XylemRemoteServices.S001XylemRemoteApproval.Progress):
				attr = getattr(XylemRemoteServices.S001XylemRemoteApproval.Progress, attr_name)
				if isinstance(attr, SimpleNamespace) and attr.code == code:
					return attr.desc
		
		def get_validation_description(code):
			for attr_name in dir(XylemRemoteServices.S001XylemRemoteApproval.Validation):
				attr = getattr(XylemRemoteServices.S001XylemRemoteApproval.Validation, attr_name)
				if isinstance(attr, SimpleNamespace) and attr.code == code:
					return attr.desc


def get_app_linked_token(token, app = None, app_code = None):
	app_code = app_code or app.description
	if app_code == Apps.A000XylemMaster.description:
		app_key = random.choice(Apps.A000XylemMaster.app_key_list)
	elif app_code == Apps.A001QAReportAndReprocess.description:
		app_key = random.choice(Apps.A001QAReportAndReprocess.app_key_list)
	elif app_code == Apps.A002SBSRejectionEntryAndRework.description:
		app_key = random.choice(Apps.A002SBSRejectionEntryAndRework.app_key_list)
	elif app_code == Apps.A003SmartAlerts.description:
		app_key = random.choice(Apps.A003SmartAlerts.app_key_list)
	elif app_code == Apps.A004ToolsManagementSystem.description:
		app_key = random.choice(Apps.A004ToolsManagementSystem.app_key_list)
	elif app_code == Apps.A005QAPatrolCheck.description:
		app_key = random.choice(Apps.A005QAPatrolCheck.app_key_list)
	elif app_code == Apps.A0064MDigitalization.description:
		app_key = random.choice(Apps.A0064MDigitalization.app_key_list)
	elif app_code == Apps.A007OEEMonitoring.description:
		app_key = random.choice(Apps.A007OEEMonitoring.app_key_list)
	elif app_code == Apps.A008HomeSchemer.description:
		app_key = random.choice(Apps.A008HomeSchemer.app_key_list)
	elif app_code == Apps.A009BuildingManagementSystem.description:
		app_key = random.choice(Apps.A009BuildingManagementSystem.app_key_list)
	elif app_code == Apps.A010PokaYokeMonitoring.description:
		app_key = random.choice(Apps.A010PokaYokeMonitoring.app_key_list)

	token_list = list(token)
	for offset, (char, idx) in enumerate(zip(app_key, sorted(app_key_split_indices_list))):
		token_list.insert(idx + offset, char)
	return ''.join(token_list)


def extract_app_linked_token(app_linked_token):
	app_key_chars = []
	app_linked_token_list = list(app_linked_token)
	for idx in sorted(app_key_split_indices_list):
		app_key_chars.append(app_linked_token_list.pop(idx))
	app_key = ''.join(app_key_chars)
	token = ''.join(app_linked_token_list)
	if app_key in Apps.A000XylemMaster.app_key_list:
		return Apps.A000XylemMaster, token
	elif app_key in Apps.A001QAReportAndReprocess.app_key_list:
		return Apps.A001QAReportAndReprocess, token
	elif app_key in Apps.A002SBSRejectionEntryAndRework.app_key_list:
		return Apps.A002SBSRejectionEntryAndRework, token
	elif app_key in Apps.A003SmartAlerts.app_key_list:
		return Apps.A003SmartAlerts, token
	elif app_key in Apps.A004ToolsManagementSystem.app_key_list:
		return Apps.A004ToolsManagementSystem, token
	elif app_key in Apps.A005QAPatrolCheck.app_key_list:
		return Apps.A005QAPatrolCheck, token
	elif app_key in Apps.A0064MDigitalization.app_key_list:
		return Apps.A0064MDigitalization, token
	elif app_key in Apps.A007OEEMonitoring.app_key_list:
		return Apps.A007OEEMonitoring, token
	elif app_key in Apps.A008HomeSchemer.app_key_list:
		return Apps.A008HomeSchemer, token
	elif app_key in Apps.A009BuildingManagementSystem.app_key_list:
		return Apps.A009BuildingManagementSystem, token
	elif app_key in Apps.A010PokaYokeMonitoring.app_key_list:
		return Apps.A010PokaYokeMonitoring, token


def get_progress_level_by_key(key):
	for i in progress_level_key_dict:
		if key in progress_level_key_dict[i]:
			return i
# [Xylem Remote]  -- end 

ipaddress_of_system = os.getenv("IP_ADDRESS_OF_SYSTEM")
router_ipaddress_of_system = os.getenv("ROUTER_IP_ADDRESS_OF_SYSTEM")
xylem_host_router_url = f"http://{router_ipaddress_of_system}"
xylem_host_main_url = f"http://{ipaddress_of_system}:7777"
xylem_listen_port = int(os.getenv("LISTENING_PORT_OF_SYSTEM"))
a009_wc_com_port = os.getenv("A009_WC_COM_PORT")
a009_pc_com_port = os.getenv("A009_PC_COM_PORT")
a000_soc_maintenance_space_url = os.getenv("XYLEM_MAINTENANCE_SPACE_URL")
a007_oee_eve_space_url = os.getenv("A007_OEE_EVE_SPACE_URL")
a007_hrly_prod_space_url = os.getenv("A007_HOURLY_PROD_SPACE_URL")
a007_prod_ch_ov_space_url = os.getenv("A007_PROD_CH_OV_SPACE_URL")
a007_manu_com_space_url = os.getenv("A007_MANU_COM_SPACE_URL")
a007_test_oee_eve_space_url = os.getenv("A007_TEST_OEE_EVE_SPACE_URL")
xylem_remote_hosting_name = os.getenv("XYLEM_REMOTE_HOSTING_NAME")
xylem_remote_ws_pass_key = os.getenv("XYLEM_REMOTE_WEBSOCKET_PASSKEY")



xylem_background_worker_host_name = "http://127.0.0.1:5002"
#background tasks urls
a001_mainserver_connect_url =  f'/{Apps.A001QAReportAndReprocess.name}/main_server/mainserver_connect/'
a001_mainserver_get_data_url =  f'/{Apps.A001QAReportAndReprocess.name}/main_server/mainserver_get_data/'
a001_mainserver_update_data_url =  f'/{Apps.A001QAReportAndReprocess.name}/main_server/mainserver_update_data/'
a006_get_four_m_mail_url = f'/{Apps.A0064MDigitalization.name}/get_four_m_mail_url/'
a007_get_dashboard_dict_url = f'/{Apps.A007OEEMonitoring.name}/get_dashboard_dict/'
a007_get_dashboard_report_dict_url = f'/{Apps.A007OEEMonitoring.name}/get_dashboard_report_dict/'
a009_get_pc_dashboard_dict_url = f'/{Apps.A009BuildingManagementSystem.name}/get_pc_dashboard_dict/'
a009_get_wc_dashboard_dict_url = f'/{Apps.A009BuildingManagementSystem.name}/get_wc_dashboard_dict/'
a010_get_poka_yoke_tree_dict_of_pc_url = f'/{Apps.A010PokaYokeMonitoring.name}/get_poka_yoke_tree_dict_of_pc/'
a010_get_poka_yoke_fruit_clusters_dict_url = f'/{Apps.A010PokaYokeMonitoring.name}/get_poka_yoke_fruit_clusters_dict/'
a010_get_poka_yoke_fruits_dict_url = f'/{Apps.A010PokaYokeMonitoring.name}/get_poka_yoke_fruits_dict/'

if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
	a007_max_no_of_lines_in_update_dashboard_dict = 1 # maximum is 10. high value results in high cpu usage.

	# xylem remote settings
	xylem_hosting_name = "127.0.0.1:8000"
	xylem_remote_hosting_name = "192.168.1.104:8001"
	# xylem_remote_hosting_name = "127.0.0.1:8001"
	# xylem_remote_hosting_name = "xylemremote.com"
	xylem_remote_approval_url = f"http://{xylem_remote_hosting_name}/s001/{{token}}/{{response}}"
	fourm_approval_url = (f"http://{xylem_hosting_name}/a006/approvals/four_m_approval/"f"{get_first_pagination_option().icode}/1/{{fourm_id}}")
	xylem_remote_ws_uri = f"ws://{xylem_remote_hosting_name}/ws/socket-server/"
	xyelm_remote_ws_session_timeout_in_secs = 60

elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
	a007_max_no_of_lines_in_update_dashboard_dict = 1 # maximum is 10. high value results in high cpu usage.

	# xylem remote settings
	# xylem_remote_hosting_name = "10.173.3.72:8001"
	# xylem_remote_hosting_name = "127.0.0.1:8001"
	xylem_remote_hosting_name = "xylemremote.com"
	xylem_remote_approval_url = f"http://{xylem_remote_hosting_name}/s001/{{token}}/{{response}}"
	xylem_remote_ws_uri = f"ws://{xylem_remote_hosting_name}/ws/socket-server/"
	xyelm_remote_ws_session_timeout_in_secs = 60

elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
	a007_max_no_of_lines_in_update_dashboard_dict = 5 # maximum is 10. high value results in high cpu usage.

	# xylem remote settings
	xylem_remote_hosting_name = "xylemremote.com"
	xylem_hosting_name = "10.173.3.12:7777"
	fourm_approval_url = (f"http://{xylem_hosting_name}/a006/approvals/four_m_approval/"f"{get_first_pagination_option().icode}/1/{{fourm_id}}")
	xylem_remote_approval_url = f"https://{xylem_remote_hosting_name}/s001/{{token}}/{{response}}"
	xylem_remote_ws_uri = f"wss://{xylem_remote_hosting_name}/ws/socket-server/"
	xyelm_remote_ws_session_timeout_in_secs = 60