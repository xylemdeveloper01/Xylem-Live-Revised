import json, socket, time, datetime, queue, requests, schedule, copy, textwrap, logging, threading
from django.db.utils import ProgrammingError
from django.utils import timezone
from django.db.models import Q, F, Sum, When, Case, Value, Avg, Max
from django.db.models.functions import Coalesce
from django.db import transaction
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.core.cache import caches
from threading import Event, Semaphore

from xylem.settings import EMAIL_HOST_USER, XYLEM_MODE, XYLEM_MODE_DIC
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.background_works.main_socket import a007_app_to_client_queue, a007_client_to_app_queue, communication_dict
from xylem_apps.a002_sbs_rejection_entry_and_rework.models import RejectionReworkEntryData
from xylem_apps.a007_oee_monitoring.models import minutes_period, pq_hp_list, max_minute_period, ProductionData, IdleEvents, ProductionChangeOvers, OEEData, ProductionPlan

a007_bw_logger = logging.getLogger(serve.Apps.A007OEEMonitoring.bw_logger_name)
a007_cache = caches[serve.an_oee_monitoring]

prod_data_queue = queue.Queue(maxsize=30)
oee_eve_queue = queue.Queue(maxsize=30)
change_over_queue = queue.Queue(maxsize=30)
change_over_chat_queue = queue.Queue(maxsize=30)
oee_eve_chat_queue = queue.Queue(maxsize=30)
manu_com_chat_queue=queue.Queue(maxsize=30)
test_oee_eve_id_chat_queue=queue.Queue(maxsize=30)


hourly_production_chat_event = threading.Event()


shift_end_eve = Event()
pq_hp_index = None

oee_dict = {}
oee_dashboard_dict = {}
oee_ps_pl_dict = {}
break_eve_handler_dic={}
oee_hmi_popup_list = []
oee_hmi_popdown_list = []
m3al_text_wrap_len_in_mail = 20
m5al_text_wrap_len_in_dashboard = 20


# where_id_ps:  where id of production station from which data taken , ini_t:initial time, ini_dt:initial datetime, npq: new production quantity, opq: old production quantity,
# rpn: running part number, rpn_ct: running part number's cycle time, rpn_i: running part number's icode object,og_it: on going idletime
# pq_hp_i: production quantity hour period index, oee_eve_cap_trig: oee event capture trigger
# manu_com_msg_sent_status: manual communication message sent
# spq: shift production quantity,
# spq_upto_lcho: shift production quantity last change over, last_chg_ov_t: last change over time, lu_m5al_list: last updated m5al list
# pl_bg_c: production line background color, pl_txt_c: production line txt color
# cho_rpq: change over reference production quantity, prod_intrpt_flag: production interrupt flag, hmi_repopup_flag: HMI repopup flag if line is reconnected
# poec: planned OEE events count

sub_dict_default = {
	"where_id_ps": None, "ini_t": None, "ini_dt": None, "npq": None, "opq": None, "rpn": None, "rpn_ct":None, "rpn_i":None, "og_it": None, "pq_hp_i": None,
	"oee_eve_cap_trig": None, "manu_com_msg_sent_status": None,
	"spq": None, "spq_upto_lcho": None, "last_chg_ov_t": None, "lu_m5al_list":[], "pl_bg_c": None, "pl_txt_c": None, "cho_rpq": None,
	"prod_intrpt_flag": None, "hmi_repopup_flag": None, "poec": None
}

# pl_n : production line name, pl_bg_c : production line background color, pl_txt_c : production line text color,
# grr : gear run, it_s : idle time string, tt : time text, ddst : date day shift text
# oee_p : oee percentage, oee_p_bc: oee percentage background color, oee_ps : oee percentage in string
# tot_avl_t : total available time, pdt : planned down time, avg_ct : average cycle time
# avl_p : availability percentage, avl_p_bc: availability percentage background color, avl_ps : availability percentage in string, at_pl : availability table plan, at_ac : availability table actual
# avl_ls : availability loss string, avl_ls_bc : availability loss string background color, avl_ls_tc : availability loss string text color, perf_p : performance percentage, perf_p_bc: performance percentage background color, perf_ps : performance percentage in string
# pt_pp :performance table production plan, pt_pa :performance table production actual, perf_ls : performance loss string, perf_ls_bc : performance loss string background color, perf_ls_tc : performance loss string text color, qa_p : quality percentage, qa_p_bc: quality percentage background color
# qa_ps : quality percentage in string, qt_okp : quality table ok parts, qt_rej_rew : quality table rejections and reworks, qa_ls : quality loss string, qa_ls_bc : quality loss string background color, qa_ls_tc : quality loss string text color
# ct_s_ot : cummulative table shift oee text, ct_s_otc : cummulative table shift oee text color, ct_s_obc : cummulative table shift oee background color
# ct_s_ct_pl : cummulative table shift cycle time plan, ct_s_at : cummulative table shift actual text, ct_s_atc : cummulative table shift actual text color, ct_s_abc : cummulative table shift actual background color,
# ct_s_ppc_pl : cummulative table shift ppc plan
# ct_d_ot : cummulative table day oee text, ct_d_otc : cummulative table day oee text color, ct_d_obc : cummulative table day oee background color
# ct_d_ct_pl : cummulative table day cycle time plan, ct_d_at : cummulative table day actual text, ct_d_atc : cummulative table day actual text color, ct_d_abc : cummulative table day actual background color,
# ct_d_ppc_pl : cummulative table day ppc plan
# ct_m_ot : cummulative table month oee text, ct_m_otc : cummulative table month oee text color, ct_m_obc : cummulative table month oee background color
# ct_m_ct_pl : cummulative table month cycle time plan, ct_m_at : cummulative table month actual text, ct_m_atc : cummulative table month actual text color, ct_m_abc : cummulative table month actual background color,
# ct_m_ppc_pl : cummulative table month ppc plan
# hrly : hourly production chart ==> xn : x axis name, y : y axis value, bntt : bar name tool tip, bc : bar color, t : target value, ltt: line tool tip
# m5al : major 5 availability loss chart ==> x : x axis value, yn : y axis name, bn : bar name, bc : bar color
# wf : waterfall chart ==> xn : x axis name, y : bar value, bn : bar name, bntt : bar name tool tip, bc : bar color
# rt_p_no :  runningpart table part number, rt_p_na :  runningpart table part name, rt_cho :  runningpart table change over time
# wt_wo_no :  workorder table workorder number, wt_wo_qty :  workorder table workorder quantity
# wt_wo_a_r_qty :  workorder table workorder actaul | remaining quantity
# psut_tc: prodcution split total changeovers, psut_data: prodcution split up data, slide_timeout: production line slide time out for the dashboard

sub_oee_dashboard_dict_default = {
	"pl_n": "",
	"pl_bg_c": "",
	"pl_txt_c": "",
	"grr": None,
	"it_s": "",
	"tt": "",
	"ddst": "",
	"color_code_dict": serve.color_code_dict,
	"oee_p": 0,
	"oee_p_bc": "",
	"oee_ps": "0%",
	"tot_avl_t": 0,
	"pdt": 0,
	"avg_ct": 0,
	"avl_p": 0,
	"avl_p_bc": "",
	"avl_ps": "0%",
	"at_pl": "",
	"at_ac": "",
	"avl_ls": "",
	"avl_ls_bc": "",
	"avl_ls_tc": "",
	"perf_p": 0,
	"perf_p_bc": "",
	"perf_ps": "0%",
	"pt_pp": 0,
	"pt_pa": 0,
	"perf_ls": "",
	"perf_ls_bc": "",
	"perf_ls_tc": "",
	"qa_p": 0,
	"qa_p_bc": "",
	"qa_ps": "0%",
	"qt_okp": 0,
	"qt_rej_rew": 0,
	"qa_ls": "",
	"qa_ls_bc": "",
	"qa_ls_tc": "",
	"ct_s_ot": "",
	"ct_s_otc": "",
	"ct_s_obc": "",
	"ct_s_ct_pl": 0,
	"ct_s_at": 0,
	"ct_s_atc": "",
	"ct_s_abc": "",
	"ct_s_ppc_pl": 0,
	"ct_d_ot": "",
	"ct_d_otc": "",
	"ct_d_obc": "",
	"ct_d_ct_pl": 0,
	"ct_d_at": 0,
	"ct_d_atc": "",
	"ct_d_abc": "",
	"ct_d_ppc_pl": 0,
	"ct_m_ot": "",
	"ct_m_otc": "",
	"ct_m_obc": "",
	"ct_m_ct_pl": 0,
	"ct_m_at": 0,
	"ct_m_atc": "",
	"ct_m_abc": "",
	"ct_m_ppc_pl": 0,
	"hrly": {
		"xn": [],
		"y": [],
		"bntt": [],
		"bc": [],
		"t": [],
		"ltt": [],
	},
	"m5al":{
		"x": [],
		"yn": [],
		"bc": [],
		"bn": [],
	},
	"wf": {
		"xn": [],
		"y": [],
		"bn": [],
		"bntt": [],
		"bc": [],
	},
	"rt_p_no": "",
	"rt_p_na": "WIP", #NA
	"rt_cho": "",
	"wt_wo_no": "WIP",
	# "wt_wo_no": 25012023pt_pa2, #NA
	"wt_wo_qty": "WIP",
	# "wt_wo_qty": 520, #NA
	"wt_wo_a_r_qty": "WIP",
	# "wt_wo_a_r_qty": "270 | 250", #NA,
	"psut_tc": 0,
	"psut_data": "",
	"time_bar": [],
	"slide_timeout": 0
}

# dt:  date text, dst: date shift text
sub_oee_dashboard_report_dict_default = {
	"pl_n": "",
	"pl_bg_c": "",
	"pl_txt_c": "",
	"dt": "",
	"dst": "",
	"color_code_dict": serve.color_code_dict,
	"oee_p": 0,
	"oee_p_bc": "",
	"oee_ps": "0%",
	"tot_avl_t": 0,
	"pdt": 0,
	"avg_ct": 0,
	"avl_p": 0,
	"avl_p_bc": "",
	"avl_ps": "0%",
	"at_pl": "",
	"at_ac": "",
	"avl_ls": "",
	"avl_ls_bc": "",
	"avl_ls_tc": "",
	"perf_p": 0,
	"perf_p_bc": "",
	"perf_ps": "0%",
	"pt_pp": 0,
	"pt_pa": 0,
	"perf_ls": "",
	"perf_ls_bc": "",
	"perf_ls_tc": "",
	"qa_p": 0,
	"qa_p_bc": "",
	"qa_ps": "0%",
	"qt_okp": 0,
	"qt_rej_rew": 0,
	"qa_ls": "",
	"qa_ls_bc": "",
	"qa_ls_tc": "",
	"ct_s_ot": "",
	"ct_s_otc": "",
	"ct_s_obc": "",
	"ct_s_ct_pl": 0,
	"ct_s_at": 0,
	"ct_s_atc": "",
	"ct_s_abc": "",
	"ct_s_ppc_pl": 0,
	"ct_d_ot": "",
	"ct_d_otc": "",
	"ct_d_obc": "",
	"ct_d_ct_pl": 0,
	"ct_d_at": 0,
	"ct_d_atc": "",
	"ct_d_abc": "",
	"ct_d_ppc_pl": 0,
	"ct_m_ot": "",
	"ct_m_otc": "",
	"ct_m_obc": "",
	"ct_m_ct_pl": 0,
	"ct_m_at": 0,
	"ct_m_atc": "",
	"ct_m_abc": "",
	"ct_m_ppc_pl": 0,
	"hrly": {
		"xn": [],
		"y": [],
		"bntt": [],
		"bc": [],
		"t": [],
		"ltt": [],
	},
	"m5al":{
		"x": [],
		"yn": [],
		"bn": [],
	},
	"wf": {
		"xn": [],
		"y": [],
		"bn": [],
		"bntt": [],
		"bc": [],
	},
	"wt_wo_no": "WIP",
	# "wt_wo_no": 25012023pt_pa2, #NA
	"wt_wo_qty": "WIP",
	# "wt_wo_qty": 520, #NA
	"wt_wo_a_r_qty": "WIP",
	# "wt_wo_a_r_qty": "270 | 250", #NA,
	"psut_tc": 0,
	"psut_data": "",
	"time_bar": [],
}


current_time_time = time.time()
current_time_datetime = datetime.datetime.now()


def routine_work():
	global pq_hp_index, current_time_time, current_time_datetime
	while True:
		current_time_time = time.time()
		current_time_datetime = datetime.datetime.now()
		temp_current_dt = current_time_datetime
		pq_hp_index = int(temp_current_dt.hour*60/minutes_period) + int(temp_current_dt.minute/minutes_period)
		time.sleep(.2)


def data_encode():
	while True:
		if not shift_end_eve.is_set():
			for where_id_pl in oee_dict:
				where_id_ps = oee_dict[where_id_pl]["where_id_ps"]
				temp_byte = b''
				if oee_dict[where_id_pl]["oee_eve_cap_trig"]:
					a007_bw_logger.info(f"{serve.an_oee_monitoring}: Poped up {where_id_pl}")
					temp_byte = temp_byte + serve.soc_a007_oee_eve_cap_sign_byte + where_id_ps.to_bytes(serve.soc_a000_where_id_byte_len, 'big') + serve.soc_a007_oee_eve_cap_sign_popup_byte
					if not where_id_pl in oee_hmi_popup_list:
						oee_hmi_popup_list.append(where_id_pl)
					oee_dict[where_id_pl]["oee_eve_cap_trig"] = False
				if where_id_pl in oee_hmi_popup_list:
					temp_byte = temp_byte + serve.soc_a000_production_interrupt_sign_byte +\
						where_id_ps.to_bytes(serve.soc_a000_where_id_byte_len, 'big') +\
						serve.soc_a000_production_interrupt_sign_up_byte  +\
						len(serve.a007_production_interrupt_msg_byte).to_bytes(1, 'big') + serve.a007_production_interrupt_msg_byte
					if not oee_dict[where_id_pl]["prod_intrpt_flag"]:
						oee_dict[where_id_pl]["prod_intrpt_flag"] = True
				elif oee_dict[where_id_pl]["prod_intrpt_flag"] and communication_dict[where_id_ps]["soc_connection"]:
					temp_byte = temp_byte + serve.soc_a000_production_interrupt_sign_byte +\
						where_id_ps.to_bytes(serve.soc_a000_where_id_byte_len, 'big') +\
						serve.soc_a000_production_interrupt_sign_down_byte
					oee_dict[where_id_pl]["prod_intrpt_flag"] = False
				if (not communication_dict[where_id_ps]["soc_connection"]) and where_id_pl in oee_hmi_popup_list and (not oee_dict[where_id_pl]["hmi_repopup_flag"]):
					oee_dict[where_id_pl]["hmi_repopup_flag"] = True
				if communication_dict[where_id_ps]["soc_connection"] and oee_dict[where_id_pl]["hmi_repopup_flag"]:
					if where_id_pl in oee_hmi_popup_list:
						a007_bw_logger.info(f"{serve.an_oee_monitoring}: Repoped up {where_id_pl}")
						temp_byte = temp_byte + serve.soc_a007_oee_eve_cap_sign_byte + where_id_ps.to_bytes(serve.soc_a000_where_id_byte_len, 'big') + serve.soc_a007_oee_eve_cap_sign_popup_byte
					oee_dict[where_id_pl]["hmi_repopup_flag"] = False
				if not oee_dict[where_id_pl]["manu_com_msg_sent_status"] is None:
					temp_byte = temp_byte + serve.soc_a007_manu_com_sign_byte + where_id_ps.to_bytes(serve.soc_a000_where_id_byte_len, 'big') + oee_dict[where_id_pl]["manu_com_msg_sent_status"].to_bytes(1, 'big')
					a007_bw_logger.info(f"{serve.an_oee_monitoring}: Manu msg send {where_id_pl} status {oee_dict[where_id_pl]['manu_com_msg_sent_status']}")
					oee_dict[where_id_pl]["manu_com_msg_sent_status"] = None
				if where_id_pl in oee_hmi_popdown_list:
					a007_bw_logger.info(f"{serve.an_oee_monitoring}: Poped down {where_id_pl}")
					temp_byte = temp_byte + serve.soc_a007_oee_eve_cap_sign_byte + where_id_ps.to_bytes(serve.soc_a000_where_id_byte_len, 'big') + serve.soc_a007_oee_eve_cap_sign_popdown_byte
					oee_hmi_popdown_list.remove(where_id_pl)
				if temp_byte:
					a007_app_to_client_queue.put([where_id_ps,temp_byte])				
		else:
			a007_bw_logger.info(f"{serve.an_oee_monitoring}: shift end event set, skipping app data")
		time.sleep(1)


def data_decode():
	logged_flag = False
	while True:
		try:
			raw_data = a007_client_to_app_queue.get()
			if not shift_end_eve.is_set():
				sign = raw_data.pop(0)
				if sign == serve.soc_a000_prod_data_sign:
					where_id_pl = oee_ps_pl_dict[int.from_bytes(raw_data[:serve.soc_a000_where_id_byte_len], 'big')]
					part_no_size = raw_data[serve.soc_a000_where_id_byte_len]
					rpn = raw_data[serve.soc_a000_where_id_byte_len+1:][:part_no_size].decode().strip() or "Dummy"
					pq_size = raw_data[serve.soc_a000_where_id_byte_len+1+part_no_size]
					pq = int.from_bytes(raw_data[serve.soc_a000_where_id_byte_len+1+part_no_size+1:][:pq_size], 'big')
					if oee_dict[where_id_pl]["rpn"] != rpn:
						if oee_dict[where_id_pl]["cho_rpq"] != pq:
							cdt = current_time_datetime
							last_period_pq = 0
							if oee_dict[where_id_pl]["npq"]:
								last_period_pq = oee_dict[where_id_pl]["npq"]-oee_dict[where_id_pl]["opq"]
							rpn_i_list = serve.get_part_numbers_of_pl(production_line_id=where_id_pl).filter(Q(name__contains=rpn) | Q(name__contains= serve.remove_space(rpn)))
							if rpn_i_list.exists():
								oee_dict[where_id_pl]["rpn_i"] = rpn_i_list.last()
								oee_dict[where_id_pl]["rpn_ct"] = serve.get_ct_of_pn_on_pl(part_number=oee_dict[where_id_pl]["rpn_i"], production_line_id=where_id_pl)
							else:
								oee_dict[where_id_pl]["rpn_i"] = None
								oee_dict[where_id_pl]["rpn_ct"] = serve.get_ct_of_pn_on_pl(production_line_id=where_id_pl)
							change_over_queue.put([where_id_pl, oee_dict[where_id_pl]["rpn"], rpn, oee_dict[where_id_pl]["rpn_i"], cdt, last_period_pq])
							oee_dict[where_id_pl]["rpn"] = rpn
							oee_dict[where_id_pl]["last_chg_ov_t"] = cdt
					else:
						oee_dict[where_id_pl]["cho_rpq"] = pq
					if oee_dict[where_id_pl]["npq"] != pq:
						oee_dict[where_id_pl]["npq"] = pq
						if oee_dict[where_id_pl]["npq"] < oee_dict[where_id_pl]["opq"]:
							a007_bw_logger.warning(f'Data decode reset: {where_id_pl} ==> npq:{oee_dict[where_id_pl]["npq"]}, opq:{oee_dict[where_id_pl]["opq"]}, pq:{oee_dict[where_id_pl]["npq"]-oee_dict[where_id_pl]["opq"]}')
							oee_dict[where_id_pl]["opq"] = 0
				elif sign == serve.soc_a007_oee_eve_cap_sign: 
					where_id_pl = oee_ps_pl_dict[int.from_bytes(raw_data[:serve.soc_a000_where_id_byte_len], 'big')]
					oee_where_id = int.from_bytes(raw_data[serve.soc_a000_where_id_byte_len:][:serve.soc_a000_where_id_byte_len], 'big')
					oee_what_id = int.from_bytes(raw_data[2*serve.soc_a000_where_id_byte_len:][:serve.soc_a000_what_id_byte_len], 'big')
					if where_id_pl in oee_hmi_popup_list:
						oee_hmi_popup_list.remove(where_id_pl)
						oee_eve_queue.put(["A", where_id_pl, {"oee_where_id":oee_where_id, "oee_what_id":oee_what_id}])
						oee_eve_chat_queue.put(["A", where_id_pl, {"oee_where_id":oee_where_id, "oee_what_id":oee_what_id}])
					else:
						test_oee_eve_id_chat_queue.put([where_id_pl, oee_where_id, oee_what_id, True])
				elif sign == serve.soc_a007_manu_com_sign: 
					where_id_pl = oee_ps_pl_dict[int.from_bytes(raw_data[:serve.soc_a000_where_id_byte_len], 'big')]
					manu_com_where_id = int.from_bytes(raw_data[serve.soc_a000_where_id_byte_len:][:serve.soc_a000_where_id_byte_len], 'big')
					manu_com_what_id = int.from_bytes(raw_data[2*serve.soc_a000_where_id_byte_len:][:serve.soc_a000_what_id_byte_len], 'big')
					manu_com_chat_queue.put([where_id_pl, manu_com_where_id, manu_com_what_id])
				elif sign == serve.soc_a007_test_oee_eve_id_chat_sign:
					where_id_pl = oee_ps_pl_dict[int.from_bytes(raw_data[:serve.soc_a000_where_id_byte_len], 'big')]
					oee_where_id = int.from_bytes(raw_data[serve.soc_a000_where_id_byte_len:][:serve.soc_a000_where_id_byte_len], 'big')
					oee_what_id = int.from_bytes(raw_data[2*serve.soc_a000_where_id_byte_len:][:serve.soc_a000_what_id_byte_len], 'big')
					test_oee_eve_id_chat_queue.put([where_id_pl, oee_where_id, oee_what_id, None])
			else:
				a007_bw_logger.info(f"{serve.an_oee_monitoring}: shift end event set, skipping client data")
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def prod_data_generator(where_id_pl):
	logged_flag = False
	while True:
		try:
			if pq_hp_index != oee_dict[where_id_pl]["pq_hp_i"]:
				if oee_dict[where_id_pl]["npq"]!=None:
					if oee_dict[where_id_pl]["npq"]-oee_dict[where_id_pl]["opq"]<0:
						a007_bw_logger.warning(f'{where_id_pl} ==> npq:{oee_dict[where_id_pl]["npq"]}, opq:{oee_dict[where_id_pl]["opq"]}, pq:{oee_dict[where_id_pl]["npq"]-oee_dict[where_id_pl]["opq"]}')
					prod_data_queue.put([oee_dict[where_id_pl]["npq"]-oee_dict[where_id_pl]["opq"], where_id_pl, oee_dict[where_id_pl]["pq_hp_i"], current_time_datetime-datetime.timedelta(seconds=10)])
					oee_dict[where_id_pl]["opq"] = oee_dict[where_id_pl]["npq"]
				oee_dict[where_id_pl]["pq_hp_i"] = pq_hp_index
			a007_cache.set(serve.Apps.A007OEEMonitoring.cache_key_of_oee_dict, oee_dict)
			time.sleep(1)
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def move_prod_data():
	logged_flag = False
	while True:
		try:
			pq, where_id_pl, pq_hp_index, dt = prod_data_queue.get()
			pd = ProductionData.objects.filter(production_line_i_id = where_id_pl, date = dt.date())
			if pd.exists():
				pdf = pd.first()
				setattr(pdf, pq_hp_list[pq_hp_index], pq)
				pdf.save()
			else:
				temp_dict = {"production_line_i_id": where_id_pl , f"{pq_hp_list[pq_hp_index]}": pq, "date": dt.date()}
				ProductionData.objects.create(**temp_dict)
			if logged_flag:
					logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error(f"Exception occurred {pq}, {where_id_pl}, {pq_hp_index}, {dt}", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def idle_time_monitor(where_id_pl, ie_min_to_reg_m, ie_l1_es_m, ie_l2_es_m, ie_l3_es_m):
	logged_flag = False
	pq_count = None
	reg_flag = None
	l1_flag = None
	l2_flag = None
	l3_flag = None
	oee_dict[where_id_pl]["ini_t"] = current_time_time
	oee_dict[where_id_pl]["ini_dt"] = current_time_datetime
	while True:
		try:
			ct_t = current_time_time
			ct_dt = current_time_datetime
			if pq_count == oee_dict[where_id_pl]["npq"]:
				idle_time = ct_t - oee_dict[where_id_pl]["ini_t"]
				if idle_time > ie_min_to_reg_m:
					if not reg_flag:
						oee_dict[where_id_pl]["oee_eve_cap_trig"] = True
						oee_eve_queue.put(["R", where_id_pl, oee_dict[where_id_pl]["ini_dt"]])
						oee_eve_chat_queue.put(["R", where_id_pl, oee_dict[where_id_pl]["ini_dt"]])
						reg_flag = True
					oee_dict[where_id_pl]["og_it"] = int(idle_time)
				else:
					if reg_flag:
						shift = serve.get_shift(ct_dt)
						temp_shift_end_dt = shift.start_date_time(ct_dt.date())
						oee_eve_queue.put(["C", where_id_pl, temp_shift_end_dt])
						oee_eve_chat_queue.put(["C", where_id_pl, temp_shift_end_dt])
						reg_flag = False
			else:
				pq_count = oee_dict[where_id_pl]["npq"]
				oee_dict[where_id_pl]["og_it"] = 0
				oee_dict[where_id_pl]["ini_t"] = ct_t + oee_dict[where_id_pl]["rpn_ct"]
				oee_dict[where_id_pl]["ini_dt"] = ct_dt + datetime.timedelta(seconds=oee_dict[where_id_pl]["rpn_ct"])
				if reg_flag:
					oee_eve_queue.put(["C", where_id_pl, ct_dt])
					oee_eve_chat_queue.put(["C", where_id_pl, ct_dt])
					reg_flag = False
			if logged_flag:
				logged_flag = False
			time.sleep(1)
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)

	
def break_eve_handler(pl_id, idle_event, break_excess_i, break_time, close_event):
	max_limit_time = idle_event.start_time + break_time
	while True:
		if current_time_datetime>=max_limit_time:
			idle_event.end_time=max_limit_time
			idle_event.save()
			IdleEvents.objects.create(production_line_i_id=pl_id, start_time=max_limit_time, where_id_i_id=pl_id, what_id_i=break_excess_i)
			break
		if close_event.is_set():
			del break_eve_handler_dic[pl_id]
			break
		time.sleep(0.1)


def oee_eve_handler():
	logged_flag = False
	while True:
		try:
			type_e, where_id_pl, dt_or_id = oee_eve_queue.get()
			if type_e=="R":
				IdleEvents.objects.create(production_line_i_id = where_id_pl, start_time = dt_or_id)
			elif type_e=="A":
				idle_event = IdleEvents.objects.filter(production_line_i_id = where_id_pl).latest("start_time")
				if dt_or_id["oee_what_id"]==serve.OEE.tea_break.icode:
					current_dt = current_time_datetime
					shift = serve.get_oee_shift(current_dt)
					custom_date = serve.get_custom_shift_date(current_dt)
					tb = get_idle_events(custom_date=custom_date, shift=shift).filter(production_line_i_id=dt_or_id["oee_where_id"], what_id_i = serve.OEE.tea_break)
					if tb.exists() and tb.count()>=shift.no_of_tb:
						idle_event.where_id_i_id = dt_or_id["oee_where_id"]
						idle_event.what_id_i = serve.OEE.tea_break_excess
						idle_event.save()
					else:
						idle_event.where_id_i_id = dt_or_id["oee_where_id"]
						idle_event.what_id_i = serve.OEE.tea_break
						idle_event.save()
						close_event = Event()
						break_han = serve.run_as_thread(break_eve_handler,args=(where_id_pl, idle_event, serve.OEE.tea_break_excess, serve.OEE.tea_break_time_duration_td, close_event,))
						break_eve_handler_dic[where_id_pl] = {"th":break_han , "close_event":close_event}
				elif dt_or_id["oee_what_id"]==serve.OEE.food_break.icode:
					current_dt = current_time_datetime
					shift = serve.get_oee_shift(current_dt)
					custom_date = serve.get_custom_shift_date(current_dt)
					fb = get_idle_events(custom_date=custom_date, shift=shift).filter(production_line_i_id=dt_or_id["oee_where_id"], what_id_i = serve.OEE.food_break)
					if fb.exists() and fb.count()>=shift.no_of_fb:
						idle_event.where_id_i_id = dt_or_id["oee_where_id"]
						idle_event.what_id_i = serve.OEE.food_break_excess
						idle_event.save()
					else:
						idle_event.where_id_i_id = dt_or_id["oee_where_id"]
						idle_event.what_id_i = serve.OEE.food_break
						idle_event.save()
						close_event = Event()
						break_han = serve.run_as_thread(break_eve_handler,args=(where_id_pl, idle_event, serve.OEE.food_break_excess, serve.OEE.food_break_duration_td, close_event,))
						break_eve_handler_dic[where_id_pl]={"th":break_han, "close_event":close_event}
				else:
					idle_event.where_id_i_id = dt_or_id["oee_where_id"]
					idle_event.what_id_i_id = dt_or_id["oee_what_id"]
					idle_event.save()
			elif type_e=="C":
				idle_event = IdleEvents.objects.filter(production_line_i_id = where_id_pl).latest("start_time")
				if where_id_pl in break_eve_handler_dic:
					if break_eve_handler_dic[where_id_pl]["th"].is_alive():
						break_eve_handler_dic[where_id_pl]["close_event"].set()
						break_eve_handler_dic[where_id_pl]["th"].join()
				idle_event.end_time = dt_or_id
				if not idle_event.where_id_i:
					idle_event.where_id_i_id = where_id_pl
					idle_event.what_id_i = serve.OEE.uncaptured_event
					if where_id_pl in oee_hmi_popup_list:
						oee_hmi_popup_list.remove(where_id_pl)
						oee_hmi_popdown_list.append(where_id_pl)
				idle_event.save()
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def change_overs_handler():
	logged_flag = False
	while True:
		try:
			where_id_pl, last_pn, rpn, rpn_i, current_dt, last_period_qty = change_over_queue.get()
			shift = serve.get_shift(current_dt)
			custom_date = serve.get_custom_shift_date(current_dt)
			temp_shift_start_dt = shift.start_date_time(custom_date)
			a007_bw_logger.info(f"{serve.an_oee_monitoring}: {where_id_pl} Production Change Over From: {last_pn}, To: {rpn}")
			if not last_pn is None:
				period_start = temp_shift_start_dt
				pq_hp_dic = {}
				while period_start<current_dt:
					if not period_start.date() in pq_hp_dic:
						pq_hp_dic[period_start.date()] = []
					pq_hp_dic[period_start.date()].append(f'pq_H{period_start.hour}P{int(period_start.minute/minutes_period)}')
					period_start = period_start + datetime.timedelta(minutes=minutes_period)
				pq = 0
				for date in pq_hp_dic:
					pq_col_list = ProductionData.objects.filter(date=date, production_line_i_id=where_id_pl).values_list(*pq_hp_dic[date]).first() or []
					pq = pq + sum(filter(None, pq_col_list))
				pq = pq + last_period_qty
				cho_pl = ProductionChangeOvers.objects.filter(production_line_i_id=where_id_pl)
				last_cho = cho_pl.latest("start_time")
				last_cho.end_time = current_dt
				last_cho.pq = pq - oee_dict[where_id_pl]["spq_upto_lcho"]
				last_cho.save()
				change_over_chat_queue.put([where_id_pl, last_pn, rpn, current_dt, pq])
				if not rpn:
					oee_dict[where_id_pl]["spq_upto_lcho"] = 0
					oee_dict[where_id_pl]["cho_rpq"] = 0
				else:
					oee_dict[where_id_pl]["spq_upto_lcho"] = pq

				temp_start_time = current_dt
			else:
				temp_start_time = temp_shift_start_dt
			if not rpn is None:
				if rpn_i:
					ProductionChangeOvers.objects.create(production_line_i_id=where_id_pl, start_time=temp_start_time, part_number_i=rpn_i)
				else:
					ProductionChangeOvers.objects.create(production_line_i_id=where_id_pl, start_time=temp_start_time, temp_pn=rpn)
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def get_idle_events(custom_date, shift=None):
	if shift:
		return IdleEvents.objects.filter(start_time__gte = shift.start_date_time(custom_date), start_time__lt = shift.ns_start_date_time(custom_date))
	else:
		return IdleEvents.objects.filter(
			start_time__gte = serve.Shifts.ShiftA.start_date_time(custom_date),
			start_time__lt = serve.Shifts.ShiftA.start_date_time(custom_date+datetime.timedelta(days=1),)
		)


def get_change_overs(custom_date, shift=None):
	if shift:
		return ProductionChangeOvers.objects.filter(start_time__gte = shift.start_date_time(custom_date), start_time__lt = shift.ns_start_date_time(custom_date))
	else:
		return ProductionChangeOvers.objects.filter(
			start_time__gte = serve.Shifts.ShiftA.start_date_time(custom_date),
			start_time__lt = serve.Shifts.ShiftA.start_date_time(custom_date+datetime.timedelta(days=1),)
		)


def shift_end_activity():
	try:
		shift_end_eve.set()
		a007_bw_logger.info("shift_end_activity")
		current_dt = current_time_datetime - datetime.timedelta(seconds=60)
		shift = serve.get_shift(current_dt)
		custom_date = serve.get_custom_shift_date(current_dt)
		temp_shift_start_dt = shift.start_date_time(custom_date)
		temp_next_shift_start_dt = shift.ns_start_date_time(custom_date)
		for where_id_pl in oee_dict:
			change_over_queue.put([where_id_pl, oee_dict[where_id_pl]["rpn"], None, None, temp_next_shift_start_dt - datetime.timedelta(milliseconds=1), 0])
			oee_dict[where_id_pl]["rpn"] = None
			oee_dict[where_id_pl]["rpn_i"] = None
			oee_dict[where_id_pl]["last_chg_ov_t"] = temp_next_shift_start_dt
			oee_dict[where_id_pl]["ini_t"] = time.mktime(temp_next_shift_start_dt.timetuple()) + oee_dict[where_id_pl]["rpn_ct"]
			oee_dict[where_id_pl]["ini_dt"] = temp_next_shift_start_dt + datetime.timedelta(seconds=oee_dict[where_id_pl]["rpn_ct"])
			oee_dict[where_id_pl]["og_it"] = 0
		idle_events = get_idle_events(custom_date=custom_date, shift=shift).filter(what_id_i = None)
		for ie in idle_events:
			if ie.start_time <= temp_shift_start_dt+datetime.timedelta(seconds=600):
				ie.what_id_i = serve.OEE.no_plan
			else:
				ie.what_id_i = serve.OEE.shift_windup
			ie.where_id_i = ie.production_line_i
			ie.save()
			where_id_pl = ie.production_line_i.icode
			if where_id_pl in oee_hmi_popup_list:
				oee_hmi_popup_list.remove(where_id_pl)
				oee_hmi_popdown_list.append(where_id_pl)
		shift_end_eve.clear()
	except Exception as e:
		a007_bw_logger.error("Exception occurred", exc_info=True)
		time.sleep(serve.error_wait)


def google_chat_hrly_prod():
	logged_flag = False
	while True:
		try:
			hourly_production_chat_event.wait()
			current_dt = current_time_datetime
			time.sleep(10)

			temp_current_dt = current_dt - datetime.timedelta(seconds=60)
			shift = serve.get_shift(dt=temp_current_dt)
			custom_date = serve.get_custom_shift_date(dt=temp_current_dt)
			temp_shift_start_dt = shift.start_date_time(custom_date)
			total_avl_time = current_dt - temp_shift_start_dt
			hr_no = 0
			hourly_list = []
			date_set = set([])
			temp_period_start = temp_shift_start_dt
			temp_period_end = temp_shift_start_dt

			while True:
				period_end = temp_period_end
				temp_period_end = temp_shift_start_dt + datetime.timedelta(hours=hr_no+1)
				same_hour_pq_hp_dic = {}
				if temp_period_end >= current_dt:
					ns_start_dt = shift.ns_start_date_time(custom_date)
					if ns_start_dt <= current_dt and ns_start_dt > period_end:
						period_end = ns_start_dt
						period_start = temp_period_start
						while temp_period_start < period_end:
							if not temp_period_start.date() in same_hour_pq_hp_dic:
								same_hour_pq_hp_dic[temp_period_start.date()] = []
								date_set.add(temp_period_start.date())
							same_hour_pq_hp_dic[temp_period_start.date()].append(f'pq_H{temp_period_start.hour}P{int(temp_period_start.minute/minutes_period)}')
							temp_period_start = temp_period_start + datetime.timedelta(minutes=minutes_period)
						hourly_list.append(same_hour_pq_hp_dic.copy())
					break
				else:
					period_start = temp_period_start
					while temp_period_start < temp_period_end:
						if not temp_period_start.date() in same_hour_pq_hp_dic:
							same_hour_pq_hp_dic[temp_period_start.date()] = []
							date_set.add(temp_period_start.date())
						same_hour_pq_hp_dic[temp_period_start.date()].append(f'pq_H{temp_period_start.hour}P{int(temp_period_start.minute/minutes_period)}')
						temp_period_start = temp_period_start + datetime.timedelta(minutes=minutes_period)
					hourly_list.append(same_hour_pq_hp_dic.copy())
					hr_no = hr_no + 1
			print(hourly_list)
			current_hr_period_str = f"{period_start.time().strftime('%I:%M %p')} - {period_end.time().strftime('%I:%M %p')}"
			idle_events = get_idle_events(custom_date=custom_date, shift=shift).annotate(
				temp_end_time = Case(
					When(end_time=None, then=current_dt), 
					default=F("end_time")
				),
			).annotate(idle_time=F("temp_end_time") - F("start_time"))
			change_overs = get_change_overs(custom_date=custom_date, shift=shift).annotate(
				temp_end_time = Case(
					When(end_time=None, then=current_dt), 
					default=F("end_time")
				),
			).annotate(run_time=F("temp_end_time") - F("start_time"))
			production_data_of_dates = ProductionData.objects.filter(date__in = date_set)
			temp_hrly_prod_dict = {}
			for pl_id in oee_dict:
				pl = serve.get_icode_object(pl_id)
				idle_events_pl = idle_events.filter(production_line_i_id=pl_id)
				idle_events_pl_poe = idle_events_pl.filter(what_id_i_id__in=serve.OEE.planned_oee_events)
				idle_events_pl_pdt = idle_events_pl_poe.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
				change_overs_pl = change_overs.filter(production_line_i_id=pl_id)

				temp_hrly_prod_dict[pl_id] = {"pl_n": pl.name, "pl_bg_c": oee_dict[pl_id]["pl_bg_c"], "hrly": {"xn": [], "y": [], "bc": []}, }

				for sh_pq_hp_dic in hourly_list:
					pq = 0
					for date in sh_pq_hp_dic:
						pq_col_list = production_data_of_dates.filter(date=date, production_line_i_id=pl_id).values_list(*sh_pq_hp_dic[date]).first() or []
						pq = pq + sum(filter(None, pq_col_list))
					temp_hrly_prod_dict[pl_id]["hrly"]["y"].append(pq)

				pq_actual = sum(temp_hrly_prod_dict[pl_id]["hrly"]["y"])
				summation_h_co_ct = datetime.timedelta()
				if change_overs_pl.exists():
					co_hour_format = change_overs_pl.filter(start_time__lte = period_end, temp_end_time__gt = period_start).annotate(
						temp_h_start_time= Case(
							When(start_time__lt = period_start, then = period_start), 
							default = F("start_time")
						),
						temp_h_end_time = Case(
							When(temp_end_time__gt = period_end, then = period_end), 
							default = F("temp_end_time")
						),
						h_run_time = F("temp_h_end_time") - F("temp_h_start_time")
					)
					for hco in co_hour_format:
						pn_ct = serve.get_ct_of_pn_on_pl(part_number = hco.part_number_i, production_line = hco.production_line_i)
						summation_h_co_ct = summation_h_co_ct + hco.h_run_time*pn_ct
					h_avg_ct_pl = summation_h_co_ct/(period_end-period_start)
				else:
					h_avg_ct_pl = serve.get_ct_of_pn_on_pl(production_line_id=pl_id)
				idle_events_pl_poe_h = idle_events_pl_poe.filter(start_time__lte = period_end, temp_end_time__gt = period_start).annotate(
					temp_h_start_time = Case(
						When(start_time__lt = period_start, then = period_start), 
						default = F("start_time")
					),
					temp_h_end_time = Case(
						When(temp_end_time__gt = period_end, then = period_end), 
						default = F("temp_end_time")
					),
					h_idle_time = F("temp_h_end_time") - F("temp_h_start_time")
				).aggregate(pdt = Sum('h_idle_time'))['pdt'] or datetime.timedelta()
				temp_hour_target = int((period_end-period_start-idle_events_pl_poe_h).total_seconds()/h_avg_ct_pl)
				temp_hour_actual = temp_hrly_prod_dict[pl_id]["hrly"]["y"][-1]
				if temp_hour_target:
					temp_hour_percent = serve.convert_float_with_int_possibility((temp_hour_actual/temp_hour_target)*100,1)
				else:
					temp_hour_percent = 100
				temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_hour_percent)
				temp_hrly_prod_dict[pl_id]["hr_pq_tc"] = temp_bg_color
				
				
				idle_events_pl_poe = idle_events_pl.filter(what_id_i_id__in=serve.OEE.planned_oee_events)
				idle_events_pl_pdt = idle_events_pl_poe.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
				planned_prod_time = total_avl_time - idle_events_pl_pdt
				planned_prod_time_secs = planned_prod_time.total_seconds()
				summation_co_ct = datetime.timedelta()
				for co in change_overs_pl:
					pn_ct = serve.get_ct_of_pn_on_pl(part_number=co.part_number_i, production_line=co.production_line_i)
					co_start_time = co.start_time
					co_end_time = co.temp_end_time
					
					idle_events_pl_poe_co=idle_events_pl_poe.filter(start_time__lte=co_end_time, temp_end_time__gt=co_start_time).annotate(
						temp_co_start_time= Case(
							When(start_time__lt=co_start_time, then=co_start_time), 
							default=F("start_time")
						),
						temp_co_end_time = Case(
							When(temp_end_time__gt=co_end_time, then=co_end_time), 
							default=F("temp_end_time")
						)
					).annotate(co_idle_time=F("temp_co_end_time") - F("temp_co_start_time")).aggregate(pdt = Sum('co_idle_time'))['pdt'] or datetime.timedelta()
					summation_co_ct = summation_co_ct + (co.run_time - idle_events_pl_poe_co)*pn_ct
				avg_ct_pl = summation_co_ct/planned_prod_time or serve.get_ct_of_pn_on_pl(production_line_id=pl_id)
				pq_plan = int(planned_prod_time_secs//avg_ct_pl)

				temp_ct_plan, temp_actual = pq_plan, pq_actual
				temp_hrly_prod_dict[pl_id]["spq"] = serve.get_number_with_comma(temp_actual)
				if temp_ct_plan:
					temp_percent = (temp_actual/temp_ct_plan)*100
				else:
					temp_percent = 100
				temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_percent)
				temp_hrly_prod_dict[pl_id]["spq_tc"] = temp_bg_color
			chat_widgets = []

			comparision_arrow_head_html = ""
			if hr_no > 1:
				comparision_arrow_head_html = f"<font color='{serve.percent_high_bg_color}'>&#9650;</font><font color='{serve.percent_low_bg_color}'>&#9660;</font> with previous Hour"
			for pc in serve.get_product_categories():
				pc_head_added = False
				for pl in serve.get_production_lines(product_category=pc):
					pl_id = pl.icode
					if pl_id in temp_hrly_prod_dict:
						if not pc_head_added:
							chat_widgets.append({
								"columns": {
									"columnItems": [
										{
											"horizontalAlignment": "START",
											"widgets": [{
												"textParagraph": {
													"text": f"<b>{pc.name}</b>"
												}
											}]
										}
									]
								}
							})
							chat_widgets.append({
								"columns": {
									"columnItems": [
										{
											"horizontalAlignment": "START",
											"widgets": [{
												"textParagraph": {
													"text": "<b>Production Line</b>"
												}
											}]
										},
										{
											"horizontalAlignment": "START",
											"widgets": [{
												"textParagraph": {
													"text": f'''<b>Hour Qty [Shift Qty ]{comparision_arrow_head_html}</b>'''
												}
											}]
										}
									]
								}
							})
							pc_head_added = True
							
						pl_name = temp_hrly_prod_dict[pl_id]["pl_n"]
						pl_color = temp_hrly_prod_dict[pl_id]["pl_bg_c"]
						hr_pq = temp_hrly_prod_dict[pl_id]["hrly"]["y"][-1]
						hr_pq_tc = temp_hrly_prod_dict[pl_id]["hr_pq_tc"]
						spq = temp_hrly_prod_dict[pl_id]["spq"]
						spq_tc = temp_hrly_prod_dict[pl_id]["spq_tc"]
						comparision_arrow_html = ""
						if hr_no > 1:
							if hr_pq > temp_hrly_prod_dict[pl_id]["hrly"]["y"][-2]:
								comparision_arrow_html = f"<font color='{serve.percent_high_bg_color}'>&#9650;</font>"
							elif hr_pq < temp_hrly_prod_dict[pl_id]["hrly"]["y"][-2]:
								comparision_arrow_html = f"<font color='{serve.percent_low_bg_color}'>&#9660;</font>" 
						chat_widgets.append({
							"columns": {
								"columnItems": [
									{
										"horizontalAlignment": "START",
										"widgets": [
											{
												"textParagraph": {
													"text": f"<font color='{pl_color}'>{pl_name}</font>"
												}
											}
										]
									},
									{
										"horizontalAlignment": "START",
										"widgets": [
											{
												"textParagraph": {
													"text": (
														f"<font color='{hr_pq_tc}'>{hr_pq}</font> "
														f"<font color='{spq_tc}'>[{spq}]</font>"
														f"{comparision_arrow_html}"
													)
												}
											}
										]
									}
								]
							}
						})

			# Final Google Chat Card
			card_message = {
				"cardsV2": [
					{
						"cardId": "hourly-prod-card",
						"card": {
							"header": {
								"title": "<b><u>Hourly Intimation!</u></b>",
								"subtitle":  f"<u>{custom_date} {shift.name} {current_hr_period_str}</u>"
							},
							"sections": [
								{
									"widgets": chat_widgets,
								}
							]
						}
					}
				]
			}
			retry_count = 0
			while retry_count <= serve.chat_max_retry_count:
				try:
					data_dir = card_message
					r = requests.post(serve.a007_hrly_prod_space_url, data=json.dumps(data_dir), timeout=5)
					a007_bw_logger.info(f'{serve.an_oee_monitoring}: GCH: Google chat hourly production message sent... {current_hr_period_str} {time.strftime("%d-%m-%Y_%I.%M.%S_%p")} {pl.name}')
					break
				except Exception as e:
					a007_bw_logger.warning(f"Connection Error! Retrying... {e}")
					time.sleep(1)
					retry_count += 1
			hourly_production_chat_event.clear()
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def google_chat_oee_eve():
	logged_flag = False
	while True:
		try:
			type_c, where_id_pl, dt_or_id = oee_eve_chat_queue.get()
			pl = serve.get_icode_object(where_id_pl)
			pl_color = oee_dict[where_id_pl]["pl_bg_c"]
			if type_c=="R":
				chat_data = f'<font color=\"#ff0000\"><i><b>OEE Event Triggered</b></i>\n'\
							f'<b>Production Line: <font color=\"{pl_color}">{pl.name}</b>\n'\
							f'<font color=\"#ff0000\"><b>From Time:</b> {dt_or_id}</font>\n'
			elif type_c=="A":
				oee_where_id = serve.get_icode_object(dt_or_id["oee_where_id"])
				oee_what_id = serve.get_icode_object(dt_or_id["oee_what_id"])
				chat_data = f'<font color=\"#0000ff\"><i><b>OEE Event Captured</b></i>\n'\
							f'<b>Production Line : <font color=\"{pl_color}">{pl.name}</b>\n'\
							f'<font color=\"#0000ff\"><b>Where: {oee_where_id.name}</b>\n'\
							f'<b>What: {oee_what_id.name}</b></font>\n'
			elif type_c=="C":
				chat_data = f'<font color=\"#00ff00\"><i><b>OEE Event Closed</b></i>\n'\
							f'<b>Production Line: <font color=\"{pl_color}">{pl.name}</b>\n'\
							f'<font color=\"#00ff00\"><b>To Time:</b> {dt_or_id}</font>\n'
			retry_count = 0
			while retry_count <= serve.chat_max_retry_count:
				try:
					data_dir = {"cards": [{"sections":[{"widgets":[{"textParagraph":{ 'text':f'{chat_data}'}}]}]}]}
					r = requests.post(serve.a007_oee_eve_space_url, data=json.dumps(data_dir), timeout=5)
					a007_bw_logger.info(f'{serve.an_oee_monitoring}: GCO: Google chat oee event {type_c} message sent...{time.strftime("%d-%m-%Y_%I.%M.%S_%p")} {pl.name}')
					break
				except Exception as e:
					a007_bw_logger.warning(f"{serve.an_oee_monitoring}: GCO: Connection Error! check internet connection. Retrying to connect... \n Error: {e}")
					time.sleep(1)
					retry_count = retry_count + 1
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def google_chat_prod_ch_ov():
	logged_flag = False
	while True:
		try:
			where_id_pl, last_pn, rpn, current_dt, last_period_pq  = change_over_chat_queue.get()
			pl = serve.get_icode_object(where_id_pl)
			pl_color = oee_dict[where_id_pl]["pl_bg_c"]
			chat_data = (f'<i><b>{serve.an_oee_monitoring}: Production changeover Intimation!</b></i>\n'\
						f'<b>Production Line: <font color=\"{pl_color}">{pl.name}</b>\n'\
						f'Production changeover from the <b><u>{last_pn} [Qty:{last_period_pq}]</u></b> to <b><u>{rpn}</u></b>\n on {current_dt}')      
			retry_count = 0
			while retry_count <= serve.chat_max_retry_count:
				try:
					data_dir = {"cards": [{"sections":[{"widgets":[{"textParagraph":{ 'text':f'{chat_data}'}}]}]}]}
					r = requests.post(serve.a007_prod_ch_ov_space_url, data=json.dumps(data_dir), timeout=5)
					a007_bw_logger.info(f'{serve.an_oee_monitoring}: GCPC: Google chat production changeover message sent ...{time.strftime("%d-%m-%Y_%I.%M.%S_%p")} {pl.name}')
					break
				except Exception as e:
					a007_bw_logger.warning(f"{serve.an_oee_monitoring}: GCPC: Connection Error! check internet connection. Retrying to connect... \n Error: {e}")
					time.sleep(1)
					retry_count = retry_count + 1
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def google_chat_manu_com():
	logged_flag = False
	while True:
		try:
			where_id_pl, manu_com_where_id, manu_com_what_id = manu_com_chat_queue.get()
			pl = serve.get_icode_object(where_id_pl)
			manu_com_where = serve.get_icode_object(manu_com_where_id)
			manu_com_what = serve.get_icode_object(manu_com_what_id)
			chat_data = f'<i><b><u>{manu_com_what.name}</u></b></i>\n'\
						f'Issue location: <b><u>{manu_com_where.name}</u></b>\n'\
						f'Production Line Name: <b><u>{pl.name}</u></b>\n'
			retry_count = 0
			msg_sent_flag = None
			while retry_count <= serve.chat_max_retry_count:
				try:
					data_dir = {"cards": [{"sections":[{"widgets":[{"textParagraph":{ 'text':f'{chat_data}'}}]}]}]}
					r = requests.post(serve.a007_manu_com_space_url, data=json.dumps(data_dir), timeout=5)
					a007_bw_logger.info(f'{serve.an_oee_monitoring}: GCMC: Google chat manual communication message sent ...{time.strftime("%d-%m-%Y_%I.%M.%S_%p")} {pl.name}')
					oee_dict[where_id_pl]["manu_com_msg_sent_status"] = True
					msg_sent_flag = True
					break
				except Exception as e:
					a007_bw_logger.warning(f"{serve.an_oee_monitoring}: GCMC: Connection Error! check internet connection. Retrying to connect... \n Error: {e}")
					time.sleep(1)
					retry_count = retry_count + 1
			if not msg_sent_flag:
				oee_dict[where_id_pl]["manu_com_msg_sent_status"] = False
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def google_chat_test_oee_eve_id():
	logged_flag = False
	while True:
		try:
			where_id_pl, oee_where_id, oee_what_id, alert = test_oee_eve_id_chat_queue.get()
			pl = serve.get_icode_object(where_id_pl)
			eve_where = serve.get_icode_object(oee_where_id)
			eve_what = serve.get_icode_object(oee_what_id)
			chat_data = f'<i><b><u>{serve.an_oee_monitoring}: OEE EVE ID TEST</u></b></i>\n'\
						f'Line Name: <b><u>{pl.name}</u></b>\n'\
						f'Where : <b><u>{eve_where.name}</u></b>\n'\
						f'What : <b><u>{eve_what.name}</u></b>\n'
			if alert:
				chat_data =  chat_data + "<font color=\"#ff0000\"><i><b>Alter received without raising pop up</b></i>"
			retry_count = 0
			while retry_count <= serve.chat_max_retry_count:
				try:
					data_dir = {"cards": [{"sections":[{"widgets":[{"textParagraph":{ 'text':f'{chat_data}'}}]}]}]}
					r = requests.post(serve.a007_test_oee_eve_space_url, data=json.dumps(data_dir), timeout=5)
					a007_bw_logger.info(f'{serve.an_oee_monitoring}: GCTOEI: Google chat test oee event id message sent ...{time.strftime("%d-%m-%Y_%I.%M.%S_%p")} {pl.name}')
					break
				except Exception as e:
					a007_bw_logger.warning(f"{serve.an_oee_monitoring}: GCTOEI: Connection Error! check internet connection. Retrying to connect... \n Error: {e}")
					time.sleep(1)
					retry_count = retry_count + 1
			if logged_flag:
				logged_flag = False
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def oee_report_mail(shift=None):
	try:
		current_dt = current_time_datetime
		custom_dt = current_dt - datetime.timedelta(minutes=serve.Others.a007_wait_for_oee_report_mail_in_min, seconds=60)
		custom_date = serve.get_custom_shift_date(custom_dt)
		rows = []
		shift_name =""
		text_wrapper = textwrap.TextWrapper(width=m3al_text_wrap_len_in_mail) 
		if shift:
			shift_name =  shift.name
			subject = f"X-A007: OEE Shift Report - {custom_date} {shift_name}"
			table_color = shift.bg_color
		else:
			subject = f"X-A007: OEE Day Report {custom_date}"
			table_color = serve.Others.day_bg_color
		oee_data = OEEData.objects.filter(date = custom_date, shift = shift.shift if shift else shift)
		if not oee_data.exists():
			a007_bw_logger.info(f"{serve.an_oee_monitoring}: No oee data found, so no mail will send. {subject}")
			return 0
		oee_data_pl_id_list = []
		for data in oee_data:
			temp_dict = {}
			pl_id = data.production_line_i.icode
			oee_data_pl_id_list.append(pl_id)
			temp_dict["pl"] = {"value" : data.production_line_i.name, "bg_color": oee_dict[pl_id]["pl_bg_c"], "txt_color": oee_dict[pl_id]["pl_txt_c"]}
			temp_value = serve.convert_float_with_int_possibility(data.oee,1)
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_value)
			temp_dict["oee"] = {"value" :temp_value, "bg_color":temp_bg_color, "txt_color": temp_txt_color}
			temp_value = serve.convert_float_with_int_possibility(data.availability,1)
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_value)
			temp_dict["availability"] = {"value" :temp_value, "bg_color":temp_bg_color, "txt_color": temp_txt_color}
			temp_value = serve.convert_float_with_int_possibility(data.performance,1)
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_value)
			temp_dict["performance"] = {"value" :temp_value, "bg_color":temp_bg_color, "txt_color": temp_txt_color}
			temp_value = serve.convert_float_with_int_possibility(data.quality,1)
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_value)
			temp_dict["quality"] = {"value" :temp_value, "bg_color":temp_bg_color, "txt_color": temp_txt_color}
			temp_dict["pq_plan"] = data.pq_plan
			temp_value = serve.convert_float_with_int_possibility((data.pq_ok_p/data.pq_plan)*100,1)
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_value)
			temp_dict["pq_actual"] = {"value" :data.pq_ok_p, "bg_color":temp_bg_color, "txt_color": temp_txt_color}
			temp_dict["rej_and_rew_qty"] = data.pq_actual - data.pq_ok_p
			temp_value = serve.convert_float_with_int_possibility(data.pdt/60,1)
			temp_dict["tot_pdt"] = temp_value
			temp_value = serve.convert_float_with_int_possibility(data.updt/60,1)
			temp_dict["tot_updt"] = temp_value
			temp_dict["tot_le"] = data.tot_le
			rows.append(temp_dict.copy())
		no_production_lines_list = []
		for pl_id in oee_dict:
			if not pl_id in oee_data_pl_id_list:
				no_production_lines_list.append(pl_id)
		for index_i, i in enumerate(no_production_lines_list):
			no_production_lines_list[index_i]=serve.get_icode_object(i).name
		no_production_lines = ", ".join(no_production_lines_list)
		context = {
			"current_date": custom_date,
			"day_of_week": custom_date.strftime("%a"),
			"table_color": table_color,
			"shift_name": shift_name,
			"rows": rows,
			"no_production_lines": no_production_lines,
			"color_code_dict": serve.color_code_dict,
			"na_str": serve.na_str,
		}
		to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a007_oee_day_report_mail)
		html_content = render_to_string('a007/oee_report_mail.html', context)
		serve.send_mail(app_name = serve.an_oee_monitoring, subject = subject, to_list = to_list, html_content = html_content)
	except Exception as e:
		a007_bw_logger.error("Exception occurred", exc_info=True)
		time.sleep(serve.error_wait)


def oee_down_time_distribuition_mail(shift=None):
	try:
		current_dt = current_time_datetime
		custom_dt = current_dt - datetime.timedelta(minutes=serve.Others.a007_wait_for_dt_report_mail_in_min, seconds=60)
		custom_date = serve.get_custom_shift_date(custom_dt)
		dept_list = []
		rows = []
		shift_name = ""
		for dept in serve.OEE.depts_list:
			dept_list.append(dept.description)
		idle_events = get_idle_events(custom_date=custom_date, shift=shift).exclude(what_id_i_id__in=serve.OEE.planned_oee_events).annotate(idle_time=F("end_time") - F("start_time"))
		if shift:
			table_color = shift.bg_color
			shift_name =  shift.name
			subject = f"X-A007: Downtime Shift Report - {custom_date} {shift_name}"
		else:
			table_color = serve.Others.day_bg_color
			subject = f"X-A007: Downtime Day Report {custom_date}"
		for pl_id in oee_dict:
			pl = serve.get_icode_object(pl_id)
			captured_dt_distribution = []
			accepted_dt_distribution = []
			for dept in serve.OEE.depts_list:
				idle_events_dept = idle_events.filter(production_line_i=pl, what_id_i__in = list(serve.get_oee_events(dept_i=dept).values_list("icode",flat=True)))
				temp_cap_tit = idle_events_dept.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
				tit = serve.convert_float_with_int_possibility(temp_cap_tit.total_seconds()/60,1)
				captured_dt_distribution.append(tit)
				temp_acc_tit = idle_events_dept.filter(acceptance = True).aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
				tit = serve.convert_float_with_int_possibility(temp_acc_tit.total_seconds()/60,1)
				if temp_cap_tit == temp_acc_tit:
					dt_bg_color = serve.percent_high_bg_color
					dt_txt_color = serve.percent_high_txt_color
				else:
					dt_bg_color = serve.percent_low_bg_color
					dt_txt_color = serve.percent_low_txt_color
				accepted_dt_distribution.append({"dt": tit, "dt_bg_c": dt_bg_color, "dt_txt_c": dt_txt_color})
			pl_data = {"pl_n": pl.name, "pl_bg_c": oee_dict[pl_id]["pl_bg_c"], "pl_txt_c": oee_dict[pl_id]["pl_txt_c"]}
			rows.append([pl_data, captured_dt_distribution, accepted_dt_distribution])
			
		context = {
			"current_date": custom_date,
			"day_of_week": custom_date.strftime("%a"),
			"table_color": table_color,
			"shift_name": shift_name,
			"dept_list": dept_list,
			"color_code_dict": serve.color_code_dict,
			"rows": rows,
		}
		to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a007_downtime_day_report_mail)
		html_content = render_to_string('a007/dt_report_mail.html', context)
		serve.send_mail(app_name = serve.an_oee_monitoring, subject = subject, to_list = to_list, html_content = html_content)
	except Exception as e:
		a007_bw_logger.error("Exception occurred", exc_info=True)
		time.sleep(serve.error_wait)


def major_loss_events_of_day_mail():
	no_of_major_losses_in_mail = 10
	try:
		current_dt = current_time_datetime
		custom_dt = current_dt - datetime.timedelta(minutes=serve.Others.a007_wait_for_ml_report_mail_in_min, seconds=60)
		custom_date = serve.get_custom_shift_date(custom_dt)
		table_color = serve.Others.day_bg_color
		rows = []
		subject = f"X-A007: Major {no_of_major_losses_in_mail} Losses of Day {custom_date}"
		idle_events_upoe = get_idle_events(custom_date=custom_date).exclude(what_id_i_id__in=serve.OEE.planned_oee_events).annotate(idle_time=F("end_time") - F("start_time"))
		if not idle_events_upoe.exists():
			a007_bw_logger.info(f"A007: No loss event data found, so no mail will send. {subject}")
			return 0
		avl_loss_unique = list(idle_events_upoe.values("production_line_i", "what_id_i", "where_id_i").distinct())
		for avl_loss in avl_loss_unique:
			avl_loss["idle_time_al"]=idle_events_upoe.filter(**avl_loss).aggregate(idle_time_al= Sum("idle_time"))["idle_time_al"] or datetime.timedelta()
		avl_loss_unique_sorted = sorted(avl_loss_unique, key=lambda x:x["idle_time_al"], reverse=True)
		for avl_loss in avl_loss_unique_sorted[:no_of_major_losses_in_mail]:
			temp_dict = {}
			temp_dict["pl_id"] = avl_loss["production_line_i"]
			temp_dict["pl_bg_c"] = oee_dict[avl_loss["production_line_i"]]["pl_bg_c"]
			temp_dict["pl_txt_c"] = oee_dict[avl_loss["production_line_i"]]["pl_txt_c"]
			temp_dict["what_id"] = avl_loss["what_id_i"]
			temp_dict["where_id"] = avl_loss["where_id_i"]
			temp_dict["dept"] = serve.get_dept_of_oee_event(oee_event_id = avl_loss["what_id_i"])
			idle_time_al = int(avl_loss["idle_time_al"].total_seconds())
			mins, secs = divmod(idle_time_al, 60)
			hrs, mins = divmod(mins, 60)
			temp_str = ""
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
			temp_dict["loss_time"] = temp_str.strip()
			rows.append(temp_dict.copy())
		context = {
			"current_date": custom_date,
			"no_of_major_losses" : no_of_major_losses_in_mail,
			"table_color" : table_color,
			"day_of_week": custom_date.strftime("%a"),
			"rows": rows,
		}
		to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a007_major_losses_of_day_mail)
		html_content = render_to_string('a007/major_losses_mail.html', context)
		serve.send_mail(app_name = serve.an_oee_monitoring, subject = subject, to_list = to_list, html_content = html_content)
	except Exception as e:
		a007_bw_logger.error("Exception occurred", exc_info=True)
		time.sleep(serve.error_wait)    
 

def part_number_mail():
	try:
		current_dt = current_time_datetime
		custom_dt = current_dt - datetime.timedelta(minutes=serve.Others.a007_wait_for_pn_report_mail_in_min, seconds=60)
		custom_date = serve.get_custom_shift_date(custom_dt)
		table_color = serve.Others.day_bg_color
		rows = []
		subject = f"X-A007: Part Number Day Report {custom_date}"

		change_overs = get_change_overs(custom_date=custom_date)
		if not change_overs.exists():
			a007_bw_logger.info(f"A007: No partnumber data found, so no mail will send. {subject}")
			return 0
		pn_unique1 = list(change_overs.filter(temp_pn=None).values('part_number_i').distinct())
		for pn_dic in pn_unique1:
			pn_dic["tpq"] = change_overs.filter(**pn_dic).aggregate(tpq=Sum("pq"))["tpq"]
		pn_unique2 = list(change_overs.filter(part_number_i=None).values('temp_pn').distinct())
		for pn_dic in pn_unique2:
			pn_dic["tpq"] = change_overs.filter(**pn_dic).aggregate(tpq=Sum("pq"))["tpq"]
		pn_unique = pn_unique1 + pn_unique2
		pn_unique_sorted = sorted(pn_unique, key=lambda x:x["tpq"], reverse=True)
		for pn_dic in pn_unique_sorted:
			temp_dict = {}
			if "part_number_i"  in pn_dic:
				pn = serve.get_icode_object(pn_dic["part_number_i"])
				temp_dict["pn_name"] = pn.name 
				temp_dict["pn_tech_name"] = pn.pn_pnmt_m.technology_i.name 
				temp_dict["pn_desc"] = pn.description
			else:
				temp_dict["pn_name"] = pn_dic["temp_pn"]
				temp_dict["pn_tech_name"] = serve.na_str
				temp_dict["pn_desc"] = serve.na_str
			temp_dict["pn_actual"] = pn_dic["tpq"]
			rows.append(temp_dict.copy())
		context = {
			"current_date": custom_date,
			"table_color" : table_color,
			"day_of_week": custom_date.strftime("%a"),
			"color_code_dict": serve.color_code_dict,
			"rows": rows,
		}
		text_content = ""
		to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a007_part_number_day_report_mail)
		html_content = render_to_string('a007/pn_report_mail.html', context)
		serve.send_mail(app_name = serve.an_oee_monitoring, subject = subject, to_list = to_list, html_content = html_content)
	except Exception as e:
		a007_bw_logger.error("Exception occurred", exc_info=True)
		time.sleep(serve.error_wait)    


def production_plan_vs_actual_mail():
	try:
		current_dt = current_time_datetime
		custom_dt = current_dt - datetime.timedelta(minutes=serve.Others.a007_wait_for_plan_vs_actual_report_mail_in_min, seconds=60)
		custom_date = serve.get_custom_shift_date(custom_dt)
		rows = []
		month_year_text = custom_date.strftime("%b %Y")
		subject = f"X-A007: Production Plan Vs Actual for {month_year_text}"
		oee_month_data = OEEData.objects.filter(Q(date__month=custom_date.month, date__year=custom_date.year) & ~Q(shift=None))
		pp_month_data = ProductionPlan.objects.filter(plan_date__month=custom_date.month, plan_date__year=custom_date.year)
		for pl_id in oee_dict:
			pl_dict = {"value" : serve.get_icode_object(pl_id).name, "bg_color": oee_dict[pl_id]["pl_bg_c"], "txt_color": oee_dict[pl_id]["pl_txt_c"]}
			pp_month_data_pl = pp_month_data.filter(production_line_i_id=pl_id)
			month_plan, mtd_plan, day_plan, balance = 0, 0, 0, 0
			day_actual_dict, mtd_actual_dict, adhernence_dict, mtd_gap_dict, days_dict = {}, {}, {}, {}, {}
			if pp_month_data_pl.exists():
				last_revision = pp_month_data_pl.aggregate(last_revision = Max("revision"))["last_revision"]
				pp_month_data_pl_lr = pp_month_data_pl.filter(revision = last_revision)
				month_plan = pp_month_data_pl_lr.aggregate(planned_qty_month = Coalesce(Sum("planned_qty"),0))["planned_qty_month"]
				day_plan = pp_month_data_pl_lr.filter(plan_date = custom_date).aggregate(planned_qty_day = Coalesce(Sum("planned_qty"),0))["planned_qty_day"]
				mtd_plan = pp_month_data_pl_lr.filter(Q(plan_date__lte = custom_date)).aggregate(planned_qty_mtd = Sum("planned_qty"))["planned_qty_mtd"]
				planned_days  = pp_month_data_pl.values_list("plan_date", flat = True).distinct().count()
				completed_days = pp_month_data_pl.filter(plan_date__lte = custom_date).values_list("plan_date", flat = True).distinct().count()
				days_dict = {"planned": planned_days, "completed": completed_days, "remaining": planned_days-completed_days}
			oee_month_data_pl = oee_month_data.filter(production_line_i_id = pl_id)
			oee_day_data_pl = oee_month_data_pl.filter(date = custom_date)
			day_actual = oee_day_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			if day_plan > day_actual:
				day_actual_dict = {"value": day_actual, "bg_color": serve.color_code_dict["pc_lbc"], "txt_color": serve.color_code_dict["pc_ltc"]}
			else:
				day_actual_dict = {"value": day_actual, "bg_color": serve.color_code_dict["pc_hbc"], "txt_color": serve.color_code_dict["pc_htc"]}
			mtd_actual = oee_month_data_pl.aggregate(tot_pq_actual = Coalesce(Sum("pq_ok_p"),0))["tot_pq_actual"]
			if mtd_plan > mtd_actual:
				mtd_actual_dict = {"value": mtd_actual, "bg_color": serve.color_code_dict["pc_lbc"], "txt_color": serve.color_code_dict["pc_ltc"]}
			else:
				mtd_actual_dict = {"value": mtd_actual, "bg_color": serve.color_code_dict["pc_hbc"], "txt_color": serve.color_code_dict["pc_htc"]}
			if mtd_plan:
				temp_value = serve.convert_float_with_int_possibility((mtd_actual/mtd_plan)*100,1)
				temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_value)
				adhernence_dict = {"value" : temp_value, "bg_color": temp_bg_color, "txt_color": temp_txt_color}
			if month_plan:
				mtd_gap = mtd_actual - mtd_plan
				if mtd_gap < 0:
					mtd_gap_dict = {"value": f"{serve.get_number_with_comma(mtd_gap)}", "bg_color": serve.color_code_dict["pc_lbc"], "txt_color": serve.color_code_dict["pc_ltc"]}
				elif mtd_gap > 0:
					mtd_gap_dict = {"value": f"+{serve.get_number_with_comma(mtd_gap)}", "bg_color": serve.color_code_dict["pc_hbc"], "txt_color": serve.color_code_dict["pc_htc"]}
				else:
					mtd_gap_dict = {"value": f"{mtd_gap}", "bg_color": serve.color_code_dict["pc_hbc"], "txt_color": serve.color_code_dict["pc_htc"]}
			if month_plan:
				balance = month_plan - mtd_actual
			rows.append({
				"pl": pl_dict,
				"day_plan": f"{day_plan}" if month_plan else day_plan,
				"day_actual": day_actual_dict,
				"month_plan": month_plan,
				"mtd_plan": mtd_plan,
				"mtd_actual": mtd_actual_dict,
				"adherence": adhernence_dict,
				"mtd_gap": mtd_gap_dict,
				"balance": f"{balance}" if month_plan else balance,
				"days_dict": days_dict,
			})
		context = {
			"current_date": custom_date,
			"month_year_text": month_year_text,
			"day_of_week": custom_date.strftime("%a"),
			"color_code_dict": serve.color_code_dict,
			"rows": rows,
		}
		to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a007_production_plan_vs_actual_mail)
		html_content = render_to_string('a007/production_plan_vs_actual_mail.html', context)
		serve.send_mail(app_name = serve.an_oee_monitoring, subject = subject, to_list = to_list, html_content = html_content)
	except Exception as e:
		a007_bw_logger.error("Exception occurred", exc_info=True)
		time.sleep(serve.error_wait)    


def production_day_summary_report_mail():
	try:
		current_dt = current_time_datetime
		custom_dt = current_dt - datetime.timedelta(minutes=serve.Others.a007_wait_for_oee_report_mail_in_min, seconds=60)
		custom_date = serve.get_custom_shift_date(custom_dt)
		subject = f"X-A007: Production Day Summary Report {custom_date}"
		oee_data = OEEData.objects.filter(date = custom_date)
		oee_data_pl_id_list = sorted(list(set(data.production_line_i.icode for data in oee_data)))		
		prod_day_sum_dict = {}
		for pl_id in oee_data_pl_id_list:
			pl_data = oee_data.filter(production_line_i=pl_id)  						
			prod_day_sum_dict[serve.get_icode_object(pl_id)] = {
				"bg_color": oee_dict[pl_id]["pl_bg_c"], 
				"txt_color": oee_dict[pl_id]["pl_txt_c"],
				"shiftA": pl_data.filter(shift=serve.IcodeSplitup.icode_shiftA).first(),
				"shiftB": pl_data.filter(shift=serve.IcodeSplitup.icode_shiftB).first(),
				"shiftC": pl_data.filter(shift=serve.IcodeSplitup.icode_shiftC).first(),
				"total": pl_data.filter(shift=None).first(),
			}			
		if not oee_data.exists():
			a007_bw_logger.info(f"{serve.an_oee_monitoring}: No production data found, so no mail will send. {subject}")
			return 0
		no_production_lines_list = []
		for pl_id in oee_dict:
			if not pl_id in oee_data_pl_id_list:
				no_production_lines_list.append(pl_id)			
		for index_i, i in enumerate(no_production_lines_list):
			no_production_lines_list[index_i] = serve.get_icode_object(i).name
		no_production_lines = ", ".join(no_production_lines_list)
		context = {
			"current_date": custom_date,
			"day_of_week": custom_date.strftime("%a"),
			"no_production_lines": no_production_lines,
			"color_code_dict": serve.color_code_dict,
			"na_str": serve.na_str,
			"prod_day_sum_dict": prod_day_sum_dict
		}
		to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a007_production_day_summary_mail)
		html_content = render_to_string('a007/production_day_summary_report_mail.html', context)
		serve.send_mail(app_name = serve.an_oee_monitoring, subject = subject, to_list = to_list, html_content = html_content)
	except Exception as e:
		a007_bw_logger.error("Exception occurred", exc_info=True)
		time.sleep(serve.error_wait)


def generate_oee_data(shift=None):
	try:
		oee_events_dic={}
		current_dt = current_time_datetime - datetime.timedelta(minutes=serve.Others.a007_wait_for_generate_shift_oee_in_min, seconds=60)
		custom_date = serve.get_custom_shift_date(current_dt)
		for dept in serve.OEE.depts_list:
			oee_events_dic[dept.icode] = list(serve.get_oee_events(dept_i=dept).values_list("icode", flat=True))
		idle_events = get_idle_events(custom_date=custom_date, shift=shift).annotate(idle_time=F("end_time") - F("start_time"))
		temp_oee_data_list = []
		if shift:
			temp_shift_start_dt = shift.start_date_time(custom_date)
			temp_next_shift_start_dt = shift.ns_start_date_time(custom_date)
			change_overs = get_change_overs(custom_date=custom_date, shift=shift).annotate(run_time=F("end_time") - F("start_time"))
			total_avl_time = temp_next_shift_start_dt - temp_shift_start_dt
			period_end = temp_shift_start_dt
			period_start = temp_shift_start_dt

			pq_hp_dic = {}
			while period_end != temp_next_shift_start_dt:
				if not period_end.date() in pq_hp_dic:
					pq_hp_dic[period_end.date()]=[]
				pq_hp_dic[period_end.date()].append(f'pq_H{period_start.hour}P{int(period_start.minute/minutes_period)}')
				period_end = period_start + datetime.timedelta(minutes=minutes_period)
				period_start = period_end
			for pl_id in oee_dict:
				pq_actual = 0
				idle_events_pl = idle_events.filter(production_line_i_id=pl_id)
				idle_events_pl_upoe = idle_events_pl.exclude(what_id_i_id__in=serve.OEE.planned_oee_events)
				idle_events_pl_updt = idle_events_pl_upoe.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
				idle_events_pl_poe = idle_events_pl.filter(what_id_i_id__in=serve.OEE.planned_oee_events)
				idle_events_pl_pdt = idle_events_pl_poe.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
				change_overs_pl = change_overs.filter(production_line_i_id=pl_id)

				# [Hourly Production & PQ Actual Calculation] - start
				pq_actual = 0
				for date in pq_hp_dic:
					pq_col_list = ProductionData.objects.filter(date=date, production_line_i_id=pl_id).values_list(*pq_hp_dic[date]).first() or []
					pq_actual = pq_actual + sum(filter(None, pq_col_list))
				if not pq_actual:
					a007_bw_logger.info(f"No production line id: {pl_id}, Shift: {shift}")
					continue
				# [Hourly Production & PQ Actual Calculation] - end

				# [Availability Calculation] - start
				planned_prod_time = total_avl_time - idle_events_pl_pdt
				planned_prod_time_secs = planned_prod_time.total_seconds()
				operating_time = planned_prod_time - idle_events_pl_updt
				operating_time_secs = operating_time.total_seconds()
				oee_avl = (operating_time/planned_prod_time)*100
				# [Availability Calculation] - end

				# [Performance Calculation] - start
				summation_co_ct = datetime.timedelta()
				for co in change_overs_pl:
					pn_ct = serve.get_ct_of_pn_on_pl(part_number=co.part_number_i, production_line=co.production_line_i)
					co_start_time = co.start_time
					co_end_time = co.end_time
					a007_bw_logger.info(f"pl_id: {pl_id}, co_id: {co.id} co_end_time: {co_end_time}, co_start_time: {co_start_time}, idle_events_pl_poe: {idle_events_pl_poe}")
					idle_events_pl_poe_co=idle_events_pl_poe.filter(start_time__lte=co_end_time,end_time__gt=co_start_time).annotate(
						temp_co_start_time= Case(
							When(start_time__lt=co_start_time, then=co_start_time), 
							default=F("start_time")
						),
						temp_co_end_time = Case(
							When(end_time__gt=co_end_time, then=co_end_time), 
							default=F("end_time")
						)
					).annotate(co_idle_time=F("temp_co_end_time") - F("temp_co_start_time")).aggregate(pdt = Sum('co_idle_time'))['pdt'] or datetime.timedelta()
					summation_co_ct = summation_co_ct + (co.run_time-idle_events_pl_poe_co)*pn_ct
				avg_ct_pl = summation_co_ct/planned_prod_time or serve.get_ct_of_pn_on_pl(production_line_id=pl_id)
				pq_plan = planned_prod_time_secs//avg_ct_pl
				pq_perf_plan = operating_time_secs//avg_ct_pl
				temp_pq_perf_plan = pq_perf_plan or 1
				oee_perf = (pq_actual/temp_pq_perf_plan)*100
				# [Performance Calculation] - end

				# [Quality Calculation] - start
				rej_c = RejectionReworkEntryData.objects.filter(booked_datetime__gte = temp_shift_start_dt,
					booked_datetime__lt=temp_next_shift_start_dt,
					production_line_i =  pl_id,
					part_status_i = serve.Others.rejected_part
				).count()
				rew_c = RejectionReworkEntryData.objects.filter(booked_datetime__gte = temp_shift_start_dt,
					booked_datetime__lt=temp_next_shift_start_dt,
					production_line_i =  pl_id,
					part_status_i = serve.Others.rework_in_progress
				).count()
				pq_ok_p = pq_actual - rej_c - rew_c
				oee_qa = (pq_ok_p/pq_actual)*100
				# [Quality Calculation] - end

				# [OEE Calculation] - start
				oee = (oee_avl*oee_perf*oee_qa)/10000
				# [OEE Calculation] - end

				# [Major 3 Availability Losses] - start
				avl_loss_unique = list(idle_events_pl_upoe.values("what_id_i", "where_id_i").distinct())
				for avl_loss in avl_loss_unique:
					avl_loss["idle_time_al"]=idle_events_pl.filter(**avl_loss).aggregate(idle_time_al= Sum("idle_time"))["idle_time_al"] or datetime.timedelta()
				avl_loss_unique_sorted = sorted(avl_loss_unique, key=lambda x:x["idle_time_al"], reverse=True)
				avl_loss_dict = {}
				for index_i, i in enumerate(avl_loss_unique_sorted[:3]):
					if index_i==0:
						avl_loss_dict["fm_le_where_i_id"] = avl_loss_unique_sorted[0]["where_id_i"]
						avl_loss_dict["fm_le_what_i_id"] = avl_loss_unique_sorted[0]["what_id_i"]
						avl_loss_dict["fm_le_it"] = avl_loss_unique_sorted[0]["idle_time_al"].total_seconds()
					elif index_i==1:
						avl_loss_dict["sm_le_where_i_id"] = avl_loss_unique_sorted[1]["where_id_i"]
						avl_loss_dict["sm_le_what_i_id"] = avl_loss_unique_sorted[1]["what_id_i"]
						avl_loss_dict["sm_le_it"] = avl_loss_unique_sorted[1]["idle_time_al"].total_seconds()
					else:
						avl_loss_dict["tm_le_where_i_id"] = avl_loss_unique_sorted[2]["where_id_i"]
						avl_loss_dict["tm_le_what_i_id"] = avl_loss_unique_sorted[2]["what_id_i"]
						avl_loss_dict["tm_le_it"] = avl_loss_unique_sorted[2]["idle_time_al"].total_seconds()
				# [Major 3 Availability Losses] - end

				temp_oee_data_list.append(
					OEEData(
						production_line_i_id = pl_id,
						date = custom_date,
						shift = shift.shift,
						oee = oee,
						availability = oee_avl,
						performance = oee_perf,
						quality = oee_qa,
						avl_time = total_avl_time.total_seconds(),
						pdt = idle_events_pl_pdt.total_seconds(),
						updt = idle_events_pl_updt.total_seconds(),
						pq_plan = pq_plan,
						pq_perf_plan = pq_perf_plan,
						pq_actual = pq_actual,
						pq_ok_p = pq_ok_p,
						tot_le = len(avl_loss_unique),
						**avl_loss_dict
					)
				)
				a007_bw_logger.info(f"pl_id: {pl_id} custom_date: {custom_date} shift: {shift.shift} oee: {oee}  oee_avl: {oee_avl} oee_perf: {oee_perf} oee_qa: {oee_qa}")
				a007_bw_logger.info(f"avl_time: {total_avl_time.total_seconds()} pdt: {idle_events_pl_pdt.total_seconds()} updt: {idle_events_pl_updt.total_seconds()} pq_plan: {pq_plan}")
				a007_bw_logger.info(f"pq_perf_plan: {pq_perf_plan} pq_actual: {pq_actual} tot_pq_ok_p: {pq_ok_p}")
				a007_bw_logger.info(f"tot_le: {len(avl_loss_unique)} avl_loss_dict: {avl_loss_dict}")
		else:
			oee_day_data = OEEData.objects.filter(date=custom_date)
			for pl_id in oee_dict:
				idle_events_pl = idle_events.filter(production_line_i_id=pl_id)
				idle_events_pl_upoe = idle_events_pl.exclude(what_id_i_id__in=serve.OEE.planned_oee_events)
				oee_day_data_pl = oee_day_data.filter(production_line_i_id=pl_id)
				if oee_day_data_pl.exists():
					oee_day_data_pl_dic = oee_day_data_pl.aggregate(
						tot_at = Sum("avl_time"),
						tot_pdt = Sum("pdt"),
						tot_updt = Sum("updt"),
						tot_pq_plan = Sum("pq_plan"),
						tot_pq_perf_plan = Sum("pq_perf_plan"),
						tot_pq_actual = Sum("pq_actual"),
						tot_pq_ok_p = Sum("pq_ok_p"),
					)
				else:
					a007_bw_logger.info(f"{serve.an_oee_monitoring}: No oee data found in shifts of production line id {pl_id}, so no generation of oee for the day {custom_date}")
					continue
				planned_prod_time_secs_d = oee_day_data_pl_dic["tot_at"] - oee_day_data_pl_dic["tot_pdt"]
				operating_time_secs_d = planned_prod_time_secs_d - oee_day_data_pl_dic["tot_updt"]
				oee_avl_d = (operating_time_secs_d/planned_prod_time_secs_d)*100
				oee_perf_d = (oee_day_data_pl_dic["tot_pq_actual"]/oee_day_data_pl_dic["tot_pq_perf_plan"])*100
				oee_qa_d = (oee_day_data_pl_dic["tot_pq_ok_p"]/oee_day_data_pl_dic["tot_pq_actual"])*100
				oee_d = (oee_avl_d*oee_perf_d*oee_qa_d)/10000

				# [Major 3 Availability Losses] - start
				avl_loss_unique = list(idle_events_pl_upoe.values("what_id_i", "where_id_i").distinct())
				for avl_loss in avl_loss_unique:
					avl_loss["idle_time_al"]=idle_events_pl.filter(**avl_loss).aggregate(idle_time_al= Sum("idle_time"))["idle_time_al"] or datetime.timedelta()
				avl_loss_unique_sorted = sorted(avl_loss_unique, key=lambda x:x["idle_time_al"], reverse=True)
				avl_loss_dict = {}
				for index_i, i in enumerate(avl_loss_unique_sorted[:3]):
					if index_i==0:
						avl_loss_dict["fm_le_where_i_id"] = avl_loss_unique_sorted[0]["where_id_i"]
						avl_loss_dict["fm_le_what_i_id"] = avl_loss_unique_sorted[0]["what_id_i"]
						avl_loss_dict["fm_le_it"] = avl_loss_unique_sorted[0]["idle_time_al"].total_seconds()
					elif index_i==1:
						avl_loss_dict["sm_le_where_i_id"] = avl_loss_unique_sorted[1]["where_id_i"]
						avl_loss_dict["sm_le_what_i_id"] = avl_loss_unique_sorted[1]["what_id_i"]
						avl_loss_dict["sm_le_it"] = avl_loss_unique_sorted[1]["idle_time_al"].total_seconds()
					else:
						avl_loss_dict["tm_le_where_i_id"] = avl_loss_unique_sorted[2]["where_id_i"]
						avl_loss_dict["tm_le_what_i_id"] = avl_loss_unique_sorted[2]["what_id_i"]
						avl_loss_dict["tm_le_it"] = avl_loss_unique_sorted[2]["idle_time_al"].total_seconds()
				# [Major 3 Availability Losses] - end

				temp_oee_data_list.append(
					OEEData(
						production_line_i_id = pl_id,
						date = custom_date,
						oee = oee_d,
						availability = oee_avl_d,
						performance = oee_perf_d,
						quality = oee_qa_d,
						avl_time = oee_day_data_pl_dic["tot_at"],
						pdt = oee_day_data_pl_dic["tot_pdt"],
						updt = oee_day_data_pl_dic["tot_updt"],
						pq_plan = oee_day_data_pl_dic["tot_pq_plan"],
						pq_perf_plan = oee_day_data_pl_dic["tot_pq_perf_plan"],
						pq_actual = oee_day_data_pl_dic["tot_pq_actual"],
						pq_ok_p = oee_day_data_pl_dic["tot_pq_ok_p"],
						tot_le = len(avl_loss_unique),
						**avl_loss_dict
					)
				)
				a007_bw_logger.info(f"pl_id: {pl_id} custom_date: {custom_date} oee_d: {oee_d} oee_avl_d: {oee_avl_d} oee_perf_d: {oee_perf_d} oee_qa_d: {oee_qa_d}")
				a007_bw_logger.info(f"tot_at: {oee_day_data_pl_dic['tot_at']} tot_pdt: {oee_day_data_pl_dic['tot_pdt']} tot_updt: {oee_day_data_pl_dic['tot_updt']} tot_pq_plan: {oee_day_data_pl_dic['tot_pq_plan']}")
				a007_bw_logger.info(f"tot_pq_perf_plan: {oee_day_data_pl_dic['tot_pq_perf_plan']} tot_pq_actual: {oee_day_data_pl_dic['tot_pq_actual']} tot_pq_ok_p: {oee_day_data_pl_dic['tot_pq_ok_p']}")
		OEEData.objects.bulk_create(temp_oee_data_list)
	except Exception as e:
		a007_bw_logger.error("Exception occurred", exc_info=True)
		time.sleep(serve.error_wait)


def oee_down_time_auto_acceptence():
	current_dt = current_time_datetime
	custom_dt = current_dt - datetime.timedelta(minutes=serve.Others.a007_wait_for_dt_report_mail_in_min, seconds=60)
	custom_date = serve.get_custom_shift_date(custom_dt)
	shift = serve.get_shift(custom_dt)
	idle_events = get_idle_events(custom_date=custom_date, shift=shift).filter(acceptance=None)
	for idle_event in idle_events:
		idle_event.acceptance = True
		idle_event.save()


def update_dashboard_dict():
	hour_period_last_updated_shift_id = None
	text_wrapper = textwrap.TextWrapper(width=m5al_text_wrap_len_in_dashboard) 
	wf_first_bar_xn = "Plan Time".strip().split()
	wf_og_it_bar_xn = "Curr. Idle".strip().split()
	wf_last_bar_xn = "Avl. Time".strip().split()
	oee_events_dic = {}
	logged_flag = False
	hourly_list = []
	date_set = set([])
	last_hrly_chat_hr_no = None
	while True:
		try:
			start = time.perf_counter()
			current_dt = current_time_datetime
			temp_tt = current_dt.strftime("%I:%M:%S %p")
			shift = serve.get_shift(current_dt)
			temp_ddst = " ".join([current_dt.strftime("%d-%b-%Y"), current_dt.strftime("%a"), shift.name])
			custom_date = serve.get_custom_shift_date(current_dt)
			for dept in serve.OEE.depts_list:
				oee_events_dic[dept.icode] = list(serve.get_oee_events(dept_i=dept).values_list("icode",flat=True))
			if hour_period_last_updated_shift_id != shift.icode:
				temp_hrly_xn = []
				temp_hourly_full_time_periods_list = []
				cur_hr_no = 1
				temp_shift_start_dt = shift.start_date_time(custom_date)
				temp_next_shift_start_dt = shift.ns_start_date_time(custom_date)
				period_start = temp_shift_start_dt
				period_end = temp_shift_start_dt
				while period_end != temp_next_shift_start_dt:
					period_end = period_start + datetime.timedelta(hours=1)
					if period_end>temp_next_shift_start_dt:
						period_end = temp_next_shift_start_dt
					temp_hrly_xn.append([period_start.strftime(serve.format_of_hour), "-", period_end.strftime(serve.format_of_hour)])
					period_start = period_end
				for pl_id in oee_dashboard_dict:
					oee_dashboard_dict[pl_id]["hrly"]["xn"] = temp_hrly_xn
					oee_dashboard_dict[pl_id]["hrly"]["y"] = []
					oee_dashboard_dict[pl_id]["hrly"]["bntt"] = []
					oee_dashboard_dict[pl_id]["hrly"]["t"] = []
					oee_dashboard_dict[pl_id]["hrly"]["ltt"] = []
					oee_dashboard_dict[pl_id]["hrly"]["bc"] = []
				hour_period_last_updated_shift_id = shift.icode
				period_start = temp_shift_start_dt
			total_avl_time = current_dt - temp_shift_start_dt
			temp_time_secs = int(total_avl_time.total_seconds())
			mins, secs = divmod(temp_time_secs, 60)
			hrs, mins = divmod(mins, 60)
			temp_tot_avl_str = ""
			if hrs:
				temp_tot_avl_str = f"{hrs}Hr"
				if hrs>1:
					temp_tot_avl_str = temp_tot_avl_str + "s"
			if mins:
				temp_tot_avl_str = temp_tot_avl_str + f" {mins}Min"
				if mins>1:
					temp_tot_avl_str = temp_tot_avl_str + "s"
			if secs:
				temp_tot_avl_str = temp_tot_avl_str + f" {secs}Sec"
				if secs>1:
					temp_tot_avl_str = temp_tot_avl_str + "s"
			idle_events = get_idle_events(custom_date=custom_date, shift=shift).annotate(
				temp_end_time = Case(
					When(end_time=None, then=current_dt), 
					default=F("end_time")
				),
			).annotate(idle_time=F("temp_end_time") - F("start_time"))
			change_overs = get_change_overs(custom_date=custom_date, shift=shift).annotate(
				temp_end_time = Case(
					When(end_time=None, then=current_dt), 
					default=F("end_time")
				),
			).annotate(run_time=F("temp_end_time") - F("start_time"))
			oee_month_data = OEEData.objects.filter(Q(date__month=custom_date.month , date__year=custom_date.year) & ~Q(shift=None))
			production_plan_month_data = ProductionPlan.objects.filter(Q(plan_date__lt = custom_date, plan_date__month=custom_date.month , plan_date__year=custom_date.year) | Q(plan_date=custom_date, shift__in=shift.past_shift_list+[shift.shift]))
			period_end = temp_shift_start_dt
			if len(hourly_list)>=2 and not hourly_list[-1]:
				hourly_list = hourly_list[-2:]
				hourly_list.pop()
			else:
				hourly_list = []
				date_set = set([])
			while period_end != current_dt:
				period_end = temp_shift_start_dt + datetime.timedelta(hours=cur_hr_no)
				same_hour_pq_hp_dic = {}
				if period_end >= current_dt:
					period_end = current_dt
					temp_period_start = period_start
					while temp_period_start < period_end - datetime.timedelta(minutes=minutes_period):
						if not temp_period_start.date() in same_hour_pq_hp_dic:
							same_hour_pq_hp_dic[temp_period_start.date()] = []
							date_set.add(temp_period_start.date())
						same_hour_pq_hp_dic[temp_period_start.date()].append(f'pq_H{temp_period_start.hour}P{int(temp_period_start.minute/minutes_period)}')
						temp_period_start = temp_period_start + datetime.timedelta(minutes=minutes_period)
					hourly_list.append(same_hour_pq_hp_dic.copy())
				else:
					temp_hourly_full_time_periods_list.append([period_start, period_end])
					while period_start < period_end:
						if not period_start.date() in same_hour_pq_hp_dic:
							same_hour_pq_hp_dic[period_start.date()] = []
							date_set.add(period_start.date())
						same_hour_pq_hp_dic[period_start.date()].append(f'pq_H{period_start.hour}P{int(period_start.minute/minutes_period)}')
						period_start = period_start + datetime.timedelta(minutes=minutes_period)
					hourly_list.append(same_hour_pq_hp_dic.copy())
					cur_hr_no = cur_hr_no + 1
			if last_hrly_chat_hr_no is None:
				last_hrly_chat_hr_no = cur_hr_no
			if last_hrly_chat_hr_no != cur_hr_no:
				hourly_production_chat_event.set()
				last_hrly_chat_hr_no = cur_hr_no

			hourly_time_periods_list = temp_hourly_full_time_periods_list + [[period_start, period_end]]
			production_data_of_dates = ProductionData.objects.filter(date__in = date_set)

			def update_production_line_data(pl_id):
				with semaphore:
					pq_actual = 0
					oee_dashboard_dict[pl_id]["tt"]= temp_tt
					oee_dashboard_dict[pl_id]["ddst"]= temp_ddst
					oee_dashboard_dict[pl_id]["tot_avl_t"] = temp_tot_avl_str
					og_it = oee_dict[pl_id]["og_it"]
					if og_it:
						mins, secs = divmod(og_it, 60)
						hrs, mins = divmod(mins, 60)
						temp_str = ""
						if hrs:
							temp_str = f"{hrs}Hr"
							if hrs > 1:
								temp_str = temp_str + "s"
						if mins:
							temp_str = temp_str + f" {mins}Min"
							if mins > 1:
								temp_str = temp_str + "s"
						if secs:
							temp_str = temp_str + f" {secs}Sec"
							if secs > 1:
								temp_str = temp_str + "s"
						oee_dashboard_dict[pl_id]["it_s"] = temp_str.strip()
						if oee_dashboard_dict[pl_id]["grr"]:
							oee_dashboard_dict[pl_id]["grr"]=False
					else:
						if not oee_dashboard_dict[pl_id]["grr"]:
							oee_dashboard_dict[pl_id]["grr"]=True
						if oee_dashboard_dict[pl_id]["it_s"]:
							oee_dashboard_dict[pl_id]["it_s"]=""
					
					oee_dashboard_dict[pl_id]["rt_p_no"] = oee_dict[pl_id]['rpn']
					oee_dashboard_dict[pl_id]["rt_cho"] = serve.get_standard_str_format_of_dt_or_d(oee_dict[pl_id]['last_chg_ov_t'])
					idle_events_pl = idle_events.filter(production_line_i_id=pl_id)
					idle_events_pl_upoe = idle_events_pl.exclude(what_id_i_id__in=serve.OEE.planned_oee_events)
					idle_events_pl_updt = idle_events_pl_upoe.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
					idle_events_pl_poe = idle_events_pl.filter(what_id_i_id__in=serve.OEE.planned_oee_events)
					idle_events_pl_poe_count = idle_events_pl_poe.count()
					idle_events_pl_pdt = idle_events_pl_poe.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
					change_overs_pl = change_overs.filter(production_line_i_id=pl_id)

					# [Hourly Production & PQ Actual Calculation] - start
					for index_i, sh_pq_hp_dic in enumerate(hourly_list):
						pq = 0
						if index_i==len(hourly_list)-1 or not sh_pq_hp_dic:
							if oee_dict[pl_id]["npq"]!=None:
								pq = oee_dict[pl_id]["npq"] - oee_dict[pl_id]["opq"]
						for date in sh_pq_hp_dic:
							pq_col_list = production_data_of_dates.filter(date=date, production_line_i_id=pl_id).values_list(*sh_pq_hp_dic[date]).first() or []
							pq = pq + sum(filter(None, pq_col_list))
						temp_str = f"{pq} No"
						if pq > 1:
							temp_str = temp_str + "s"
						if len(oee_dashboard_dict[pl_id]["hrly"]["y"]) != cur_hr_no:
							oee_dashboard_dict[pl_id]["hrly"]["y"].append(0)
							oee_dashboard_dict[pl_id]["hrly"]["bntt"].append("")
						index_ele = cur_hr_no - 1 - (len(hourly_list)- 1 - index_i)
						if oee_dashboard_dict[pl_id]["hrly"]["y"][index_ele] != pq:
							oee_dashboard_dict[pl_id]["hrly"]["y"][index_ele] = pq
						if oee_dashboard_dict[pl_id]["hrly"]["bntt"][index_ele] != temp_str:
							oee_dashboard_dict[pl_id]["hrly"]["bntt"][index_ele] = temp_str
					pq_actual = sum(oee_dashboard_dict[pl_id]["hrly"]["y"])
					oee_dict[pl_id]["spq"] = pq_actual
					temp_pq_actual = pq_actual or 1
					temp_hrly_bar_counts = len(oee_dashboard_dict[pl_id]["hrly"]["t"])
					for index_htp, htp in enumerate(hourly_time_periods_list):
						
						if temp_hrly_bar_counts and index_htp < temp_hrly_bar_counts - 1 and oee_dict[pl_id]["poec"] == idle_events_pl_poe_count:
							continue
						summation_h_co_ct = datetime.timedelta()
						if change_overs_pl.exists():
							co_hour_format = change_overs_pl.filter(start_time__lte = htp[1], temp_end_time__gt = htp[0]).annotate(
								temp_h_start_time= Case(
									When(start_time__lt = htp[0], then = htp[0]), 
									default = F("start_time")
								),
								temp_h_end_time = Case(
									When(temp_end_time__gt = htp[1], then = htp[1]), 
									default = F("temp_end_time")
								),
								h_run_time = F("temp_h_end_time") - F("temp_h_start_time")
							)
							for hco in co_hour_format:
								pn_ct = serve.get_ct_of_pn_on_pl(part_number = hco.part_number_i, production_line = hco.production_line_i)
								summation_h_co_ct = summation_h_co_ct + hco.h_run_time*pn_ct
							h_avg_ct_pl = summation_h_co_ct/(htp[1]-htp[0])
						else:
							h_avg_ct_pl = serve.get_ct_of_pn_on_pl(production_line_id=pl_id)
						idle_events_pl_poe_h = idle_events_pl_poe.filter(start_time__lte = htp[1], temp_end_time__gt = htp[0]).annotate(
							temp_h_start_time = Case(
								When(start_time__lt = htp[0], then = htp[0]), 
								default = F("start_time")
							),
							temp_h_end_time = Case(
								When(temp_end_time__gt = htp[1], then = htp[1]), 
								default = F("temp_end_time")
							),
							h_idle_time = F("temp_h_end_time") - F("temp_h_start_time")
						).aggregate(pdt = Sum('h_idle_time'))['pdt'] or datetime.timedelta()
						temp_hour_target = int((htp[1]-htp[0]-idle_events_pl_poe_h).total_seconds()/h_avg_ct_pl)
						temp_hour_actual = oee_dashboard_dict[pl_id]["hrly"]["y"][index_htp]
						if temp_hour_target:
							temp_hour_percent = serve.convert_float_with_int_possibility((temp_hour_actual/temp_hour_target)*100,1)
						else:
							temp_hour_percent = 100
						temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_hour_percent)
						temp_str = f"{temp_hour_target} No"
						if temp_hour_target > 1:
							temp_str = temp_str + "s"
						if len(oee_dashboard_dict[pl_id]["hrly"]["t"]) <= index_htp:
							oee_dashboard_dict[pl_id]["hrly"]["t"].append(temp_hour_target)
							oee_dashboard_dict[pl_id]["hrly"]["ltt"].append(f"{temp_str}, Adherence:{temp_hour_percent}%")
							oee_dashboard_dict[pl_id]["hrly"]["bc"].append(temp_bg_color)
							continue
						oee_dashboard_dict[pl_id]["hrly"]["t"][index_htp] = temp_hour_target
						oee_dashboard_dict[pl_id]["hrly"]["ltt"][index_htp] = f"{temp_str}, Adherence:{temp_hour_percent}%"
						oee_dashboard_dict[pl_id]["hrly"]["bc"][index_htp] = temp_bg_color
					if oee_dict[pl_id]["poec"] != idle_events_pl_poe_count:
						oee_dict[pl_id]["poec"] = idle_events_pl_poe_count
					# [Hourly Production & PQ Actual Calculation] - end

					# [Availability Calculation] - start
					temp_time_secs = int(idle_events_pl_pdt.total_seconds())
					mins, secs = divmod(temp_time_secs, 60)
					hrs, mins = divmod(mins, 60)
					temp_str = ""
					if not any([hrs, mins, secs]):
						temp_str = serve.na_str
					if hrs:
						temp_str = f"{hrs}Hr"
						if hrs > 1:
							temp_str = temp_str + "s"
					if mins:
						temp_str = temp_str + f" {mins}Min"
						if mins > 1:
							temp_str = temp_str + "s"
					if secs:
						temp_str = temp_str + f" {secs}Sec"
						if secs > 1:
							temp_str = temp_str + "s"
					oee_dashboard_dict[pl_id]["pdt"] = temp_str
					planned_prod_time = total_avl_time - idle_events_pl_pdt
					planned_prod_time_secs = round(planned_prod_time.total_seconds()) or 1
					if planned_prod_time_secs<60:
						temp_str = f"{planned_prod_time_secs}Sec"
						if planned_prod_time_secs>1:
							temp_str = temp_str + "s"
					else:
						planned_prod_time_mins = serve.convert_float_with_int_possibility(planned_prod_time_secs/60, 1)
						temp_str = f"{planned_prod_time_mins}Min"
						if planned_prod_time_mins>1:
							temp_str = temp_str + "s"
					oee_dashboard_dict[pl_id]["at_pl"]= temp_str
					operating_time = planned_prod_time - idle_events_pl_updt
					operating_time_secs = round(operating_time.total_seconds())
					if operating_time_secs<60:
						temp_str = f"{operating_time_secs}Sec"
						if operating_time_secs>1:
							temp_str = temp_str + "s"
					else:
						operating_time_mins = serve.convert_float_with_int_possibility(operating_time_secs/60, 1)
						temp_str = f" {operating_time_mins}Min"
						if operating_time_mins>1:
							temp_str = temp_str + "s"
					oee_dashboard_dict[pl_id]["at_ac"]= temp_str
					oee_avl = serve.convert_float_with_int_possibility((operating_time/planned_prod_time)*100, 1)
					oee_dashboard_dict[pl_id]["avl_p"]= oee_avl
					oee_dashboard_dict[pl_id]["avl_p_bc"], temp = serve.get_bg_txt_color_of_percent(oee_avl)
					oee_dashboard_dict[pl_id]["avl_ps"]= f"{oee_avl}%"
					avl_ls_secs = planned_prod_time_secs - operating_time_secs
					
					if avl_ls_secs:
						if avl_ls_secs < 60:
							temp_str = f"Loss: {avl_ls_secs}Sec"
							if avl_ls_secs>1:
								temp_str = temp_str + "s"
						else:
							avl_ls_mins = serve.convert_float_with_int_possibility(avl_ls_secs/60, 1)
							temp_str = f"Loss: {avl_ls_mins}Min"
							if avl_ls_mins>1:
								temp_str = temp_str + "s"
						temp_bc, temp_tc = serve.loss_bg_color, serve.loss_txt_color
					else:
						temp_str = serve.OEE.dashboard_color_code_dict["no_loss"]["name"]
						temp_bc, temp_tc = serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], serve.OEE.dashboard_color_code_dict["no_loss"]["txt_color"]
					oee_dashboard_dict[pl_id]["avl_ls"] = temp_str
					oee_dashboard_dict[pl_id]["avl_ls_bc"] = temp_bc
					oee_dashboard_dict[pl_id]["avl_ls_tc"] = temp_tc
					# [Availability Calculation] - end

					# [Performance Calculation] - start
					summation_co_ct = datetime.timedelta()
					temp_dic = {}
					oee_dashboard_dict[pl_id]["psut_tc"] = change_overs_pl.count()
					for co in change_overs_pl:
						if co.part_number_i:
							pno = co.part_number_i.name
						else:
							pno = co.temp_pn
						temp_pq = co.pq
						if temp_pq is None:
							temp_pq = pq_actual - oee_dict[pl_id]["spq_upto_lcho"]
						if pno in temp_dic:
							temp_dic[pno] = temp_dic[pno] + f' | {temp_pq} ({co.start_time.strftime("%I:%M%p")} - {co.temp_end_time.strftime("%I:%M%p")})'
						else:
							temp_dic[pno] = f'{temp_pq} ({co.start_time.strftime("%I:%M%p")} - {co.temp_end_time.strftime("%I:%M%p")})'
						pn_ct = serve.get_ct_of_pn_on_pl(part_number=co.part_number_i, production_line=co.production_line_i)
						co_start_time = co.start_time
						co_end_time = co.temp_end_time
						
						idle_events_pl_poe_co=idle_events_pl_poe.filter(start_time__lte=co_end_time, temp_end_time__gt=co_start_time).annotate(
							temp_co_start_time= Case(
								When(start_time__lt=co_start_time, then=co_start_time), 
								default=F("start_time")
							),
							temp_co_end_time = Case(
								When(temp_end_time__gt=co_end_time, then=co_end_time), 
								default=F("temp_end_time")
							)
						).annotate(co_idle_time=F("temp_co_end_time") - F("temp_co_start_time")).aggregate(pdt = Sum('co_idle_time'))['pdt'] or datetime.timedelta()
						summation_co_ct = summation_co_ct + (co.run_time - idle_events_pl_poe_co)*pn_ct
					temp_list = []
					for index_i, i in enumerate(temp_dic):
						temp_list.append(": ".join([f'{index_i+1}) {i}', str(temp_dic[i]).lower()]))
					oee_dashboard_dict[pl_id]["psut_data"] = "\n".join(temp_list)

					avg_ct_pl = summation_co_ct/planned_prod_time or serve.get_ct_of_pn_on_pl(production_line_id=pl_id)
					temp_avg_ct_pl = serve.convert_float_with_int_possibility(avg_ct_pl, 1)
					temp_str = f"{temp_avg_ct_pl}Sec"
					if temp_avg_ct_pl>1:
						temp_str = temp_str + "s"
					oee_dashboard_dict[pl_id]["avg_ct"] = temp_str
					pq_perf_plan = int(operating_time_secs//avg_ct_pl)
					oee_dashboard_dict[pl_id]["pt_pp"] = pq_perf_plan
					oee_dashboard_dict[pl_id]["pt_pa"] = pq_actual
					
					temp_pq_perf_plan = pq_perf_plan or 1
					oee_perf = serve.convert_float_with_int_possibility((pq_actual/temp_pq_perf_plan)*100,1)
					if not pq_perf_plan:
						oee_perf = 100
					temp_str = f"{oee_perf}%"
					if oee_perf>100:
						oee_perf = 100
						temp_str = f">{oee_perf}%"
					oee_dashboard_dict[pl_id]["perf_p"] = oee_perf
					oee_dashboard_dict[pl_id]["perf_p_bc"], temp = serve.get_bg_txt_color_of_percent(oee_perf)
					oee_dashboard_dict[pl_id]["perf_ps"] = temp_str
					temp_loss_qty = pq_perf_plan - pq_actual
					perf_ls = temp_loss_qty if temp_loss_qty >= 0 else 0
					if perf_ls:
						temp_str = f"Loss: {perf_ls} No"
						if perf_ls > 1:
							temp_str = temp_str + "s"
						temp_bc, temp_tc = serve.loss_bg_color, serve.loss_txt_color
					else:
						temp_str = serve.OEE.dashboard_color_code_dict["no_loss"]["name"]
						temp_bc, temp_tc = serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], serve.OEE.dashboard_color_code_dict["no_loss"]["txt_color"]
					oee_dashboard_dict[pl_id]["perf_ls"] = temp_str
					oee_dashboard_dict[pl_id]["perf_ls_bc"] = temp_bc
					oee_dashboard_dict[pl_id]["perf_ls_tc"] = temp_tc
					# [Performance Calculation] - end

					# [Quality Calculation] - start
					rej_c = RejectionReworkEntryData.objects.filter(booked_datetime__gte = temp_shift_start_dt,
						booked_datetime__lt = temp_next_shift_start_dt,
						production_line_i =  pl_id,
						part_status_i = serve.Others.rejected_part
					).count()
					rew_c = RejectionReworkEntryData.objects.filter(booked_datetime__gte = temp_shift_start_dt,
						booked_datetime__lt = temp_next_shift_start_dt,
						production_line_i =  pl_id,
						part_status_i = serve.Others.rework_in_progress
					).count()
					oee_dashboard_dict[pl_id]["qt_rej_rew"] = rej_c + rew_c
					pq_ok_p = pq_actual - rej_c - rew_c
					oee_dashboard_dict[pl_id]["qt_okp"] = pq_ok_p
					qa_ls = rej_c + rew_c
					if qa_ls:
						temp_str = f"Loss: {qa_ls} No"
						if qa_ls > 1:
							temp_str = temp_str + "s"
						temp_bc, temp_tc = serve.loss_bg_color, serve.loss_txt_color
					else:
						temp_str = serve.OEE.dashboard_color_code_dict["no_loss"]["name"]
						temp_bc, temp_tc = serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], serve.OEE.dashboard_color_code_dict["no_loss"]["txt_color"]
					oee_dashboard_dict[pl_id]["qa_ls"] = temp_str
					oee_dashboard_dict[pl_id]["qa_ls_bc"] = temp_bc
					oee_dashboard_dict[pl_id]["qa_ls_tc"] = temp_tc
					oee_qa = serve.convert_float_with_int_possibility((pq_ok_p/temp_pq_actual)*100, 1)
					if not pq_actual:
						oee_qa = 0
					oee_dashboard_dict[pl_id]["qa_p"] = oee_qa
					oee_dashboard_dict[pl_id]["qa_p_bc"], temp = serve.get_bg_txt_color_of_percent(oee_qa)
					oee_dashboard_dict[pl_id]["qa_ps"] = f"{oee_qa}%"
					# [Quality Calculation] - end

					# [OEE Calculation] - start
					oee = serve.convert_float_with_int_possibility((operating_time/planned_prod_time)*\
						(pq_actual/temp_pq_perf_plan)*\
						(oee_dashboard_dict[pl_id]["qt_okp"]/temp_pq_actual)*100, 1)
					temp_str = f"{oee}%"
					if oee>100:
						oee = 100
						temp_str = f">{oee}%"
					oee_dashboard_dict[pl_id]["oee_p"] = oee
					oee_dashboard_dict[pl_id]["oee_p_bc"], temp = serve.get_bg_txt_color_of_percent(oee)
					oee_dashboard_dict[pl_id]["oee_ps"] = temp_str
					oee_ps = temp_str
					# [OEE Calculation] - end

					# [Cumulative Data] - start
					oee_month_data_pl = oee_month_data.filter(production_line_i_id=pl_id)
					oee_month_data_pl_dic = {
						"tot_at": 0,
						"tot_pdt": 0,
						"tot_updt": 0,
						"tot_pq_plan": 0,
						"tot_pq_perf_plan": 0,
						"tot_pq_actual": 0,
						"tot_pq_ok_p": 0
					}
					oee_day_data_pl = oee_month_data_pl.filter(date=custom_date)
					oee_day_data_pl_dic = {
						"tot_at": 0,
						"tot_pdt": 0,
						"tot_updt": 0,
						"tot_pq_plan": 0,
						"tot_pq_perf_plan": 0,
						"tot_pq_actual": 0,
						"tot_pq_ok_p": 0
					}
					production_plan_month_data_pl = production_plan_month_data.filter(production_line_i_id=pl_id)
					last_revision = production_plan_month_data_pl.aggregate(last_revision = Max("revision"))["last_revision"]
					production_plan_month_data_pl_lr = production_plan_month_data_pl.filter(revision=last_revision)      
					production_plan_day_data_pl_lr = production_plan_month_data_pl_lr.filter(plan_date=custom_date)      
					production_plan_shift_data_pl_lr = production_plan_day_data_pl_lr.filter(shift=shift.shift)      
					oee_dashboard_dict[pl_id]["ct_s_ot"] = oee_ps
					temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(oee)
					oee_dashboard_dict[pl_id]["ct_s_obc"] = temp_bg_color
					oee_dashboard_dict[pl_id]["ct_s_otc"] = temp_txt_color
					pq_plan = int(planned_prod_time_secs//avg_ct_pl)
					temp_ct_plan, temp_actual = pq_plan, pq_actual
					oee_dashboard_dict[pl_id]["ct_s_ct_pl"] = serve.get_number_with_comma(temp_ct_plan)
					oee_dashboard_dict[pl_id]["ct_s_at"] = serve.get_number_with_comma(temp_actual)
					if temp_ct_plan:
						temp_percent = (temp_actual/temp_ct_plan)*100
					else:
						temp_percent = 100
					temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_percent)
					oee_dashboard_dict[pl_id]["ct_s_abc"] = temp_bg_color
					oee_dashboard_dict[pl_id]["ct_s_atc"] = temp_txt_color
					temp_ppc_plan = 0
					if production_plan_shift_data_pl_lr.exists():
						temp_ppc_plan = production_plan_shift_data_pl_lr.last().planned_qty
					oee_dashboard_dict[pl_id]["ct_s_ppc_pl"] = serve.get_number_with_comma(temp_ppc_plan)
					
					if oee_day_data_pl.exists():
						oee_day_data_pl_dic = oee_day_data_pl.aggregate(
							tot_at = Sum("avl_time"),
							tot_pdt = Sum("pdt"),
							tot_updt = Sum("updt"),
							tot_pq_plan = Sum("pq_plan"),
							tot_pq_perf_plan = Sum("pq_perf_plan"),
							tot_pq_actual = Sum("pq_actual"),
							tot_pq_ok_p = Sum("pq_ok_p"),
						)
					planned_prod_time_secs_d = oee_day_data_pl_dic["tot_at"] - oee_day_data_pl_dic["tot_pdt"] + planned_prod_time_secs
					operating_time_secs_d = planned_prod_time_secs_d - oee_day_data_pl_dic["tot_updt"] - idle_events_pl_updt.total_seconds()
					oee_avl_d = operating_time_secs_d/planned_prod_time_secs_d
					oee_perf_d = (oee_day_data_pl_dic["tot_pq_actual"] + pq_actual)/(oee_day_data_pl_dic["tot_pq_perf_plan"] + temp_pq_perf_plan)
					oee_qa_d = (oee_day_data_pl_dic["tot_pq_ok_p"] + pq_ok_p)/(oee_day_data_pl_dic["tot_pq_actual"] + temp_pq_actual)
					oee_d = serve.convert_float_with_int_possibility(oee_avl_d*oee_perf_d*oee_qa_d*100, 1)
					temp_str = f"{oee_d}%"
					if oee_d > 100:
						oee_d = 100
						temp_str = f">{oee_d}%"
					oee_dashboard_dict[pl_id]["ct_d_ot"] = temp_str
					temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(oee_d)
					oee_dashboard_dict[pl_id]["ct_d_obc"] = temp_bg_color
					oee_dashboard_dict[pl_id]["ct_d_otc"] = temp_txt_color
					temp_ct_plan, temp_actual = oee_day_data_pl_dic["tot_pq_plan"] + pq_plan, oee_day_data_pl_dic["tot_pq_actual"] + pq_actual
					oee_dashboard_dict[pl_id]["ct_d_ct_pl"] = serve.get_number_with_comma(temp_ct_plan)
					oee_dashboard_dict[pl_id]["ct_d_at"] = serve.get_number_with_comma(temp_actual)
					if temp_ct_plan:
						temp_percent = (temp_actual/temp_ct_plan)*100
					else:
						temp_percent = 100
					temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_percent)
					oee_dashboard_dict[pl_id]["ct_d_abc"] = temp_bg_color
					oee_dashboard_dict[pl_id]["ct_d_atc"] = temp_txt_color
					temp_ppc_plan = 0
					if production_plan_day_data_pl_lr.exists():
						temp_ppc_plan = production_plan_day_data_pl_lr.aggregate(tot_planned_qty = Coalesce(Sum("planned_qty"),0))["tot_planned_qty"]
					oee_dashboard_dict[pl_id]["ct_d_ppc_pl"] = serve.get_number_with_comma(temp_ppc_plan)

					if oee_month_data_pl.exists():
						oee_month_data_pl_dic = oee_month_data_pl.aggregate(
							tot_at = Sum("avl_time"),
							tot_pdt = Sum("pdt"),
							tot_updt = Sum("updt"),
							tot_pq_plan = Sum("pq_plan"),
							tot_pq_perf_plan = Sum("pq_perf_plan"),
							tot_pq_actual = Sum("pq_actual"),
							tot_pq_ok_p = Sum("pq_ok_p"),
						)

					planned_prod_time_secs_m = oee_month_data_pl_dic["tot_at"] - oee_month_data_pl_dic["tot_pdt"] + planned_prod_time_secs
					operating_time_secs_m = planned_prod_time_secs_m - oee_month_data_pl_dic["tot_updt"] - idle_events_pl_updt.total_seconds()
					oee_avl_m = operating_time_secs_m/planned_prod_time_secs_m
					oee_perf_m = (oee_month_data_pl_dic["tot_pq_actual"] + pq_actual)/(oee_month_data_pl_dic["tot_pq_perf_plan"] + temp_pq_perf_plan)
					oee_qa_m = (oee_month_data_pl_dic["tot_pq_ok_p"] + pq_ok_p)/(oee_month_data_pl_dic["tot_pq_actual"] + temp_pq_actual)
					oee_m = serve.convert_float_with_int_possibility(oee_avl_m*oee_perf_m*oee_qa_m*100, 1)
					temp_str = f"{oee_m}%"
					if oee_m > 100:
						oee_m = 100
						temp_str = f">{oee_m}%"
					oee_dashboard_dict[pl_id]["ct_m_ot"] = temp_str
					temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(oee_m)
					oee_dashboard_dict[pl_id]["ct_m_obc"] = temp_bg_color
					oee_dashboard_dict[pl_id]["ct_m_otc"] = temp_txt_color
					temp_ct_plan, temp_actual = oee_month_data_pl_dic["tot_pq_plan"] + pq_plan, oee_month_data_pl_dic["tot_pq_actual"] + pq_actual
					oee_dashboard_dict[pl_id]["ct_m_ct_pl"] = serve.get_number_with_comma(temp_ct_plan)
					oee_dashboard_dict[pl_id]["ct_m_at"] = serve.get_number_with_comma(temp_actual)
					if temp_ct_plan:
						temp_percent = (temp_actual/temp_ct_plan)*100
					else:
						temp_percent = 100
					temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_percent)
					oee_dashboard_dict[pl_id]["ct_m_abc"] = temp_bg_color
					oee_dashboard_dict[pl_id]["ct_m_atc"] = temp_txt_color
					temp_ppc_plan = 0
					if production_plan_month_data_pl_lr.exists():
						temp_ppc_plan = production_plan_month_data_pl_lr.aggregate(tot_planned_qty = Coalesce(Sum("planned_qty"),0))["tot_planned_qty"]
					oee_dashboard_dict[pl_id]["ct_m_ppc_pl"] = serve.get_number_with_comma(temp_ppc_plan)
					# [Cumulative Data] - end

					# [Major 5 Availability Losses] - start
					avl_loss_unique = list(idle_events_pl_upoe.exclude(what_id_i = None, where_id_i=None).values("what_id_i_id", "where_id_i_id").distinct())
					for avl_loss in avl_loss_unique:
						avl_loss["idle_time_al"]=idle_events_pl.filter(**avl_loss).aggregate(idle_time_al= Sum("idle_time"))["idle_time_al"] or datetime.timedelta()
					idle_events_og = idle_events_pl_upoe.filter(what_id_i = None, where_id_i=None).annotate(
						temp_where_id = F("production_line_i__icode"), 
						temp_what_id = Value(serve.OEE.ongoing_idletime.icode), 
					)
					avl_loss_unique_og = list(idle_events_og.values("temp_where_id", "temp_what_id").distinct())
					for avl_loss in avl_loss_unique_og:
						avl_loss["idle_time_al"] = idle_events_og.filter(**avl_loss).aggregate(idle_time_al= Sum("idle_time"))["idle_time_al"] or datetime.timedelta()
						avl_loss["where_id_i_id"] = avl_loss["temp_where_id"]
						avl_loss["what_id_i_id"] = avl_loss["temp_what_id"]
						del avl_loss["temp_where_id"],avl_loss["temp_what_id"]
					avl_loss_unique = avl_loss_unique + avl_loss_unique_og
					if avl_loss_unique != oee_dict[pl_id]["lu_m5al_list"]: 
						temp_list_al_x = []
						temp_list_al_yn = []
						temp_list_al_bn = []
						temp_list_al_bc = []
						for avl_loss in sorted(avl_loss_unique, key=lambda x:x["idle_time_al"], reverse=True)[:5]:
							temp_list = []
							it = serve.convert_float_with_int_possibility(avl_loss["idle_time_al"].total_seconds()/60,1)
							if avl_loss["where_id_i_id"]!=pl_id:
								temp_list.append(serve.get_icode_object(avl_loss["where_id_i_id"]).name)
							temp_what_id_i = serve.get_icode_object(avl_loss["what_id_i_id"])
							temp_list.append(temp_what_id_i.name) 
							temp_list_al_x.append(it)
							temp_list_al_yn.append(text_wrapper.fill(" - ".join(temp_list)).strip().splitlines())
							temp_list_al_bn.append(f"{it}Mins")
							temp_bc = ""
							if temp_what_id_i.icode in [serve.OEE.ongoing_idletime.icode, serve.OEE.uncaptured_event]:
								temp_bc = serve.OEE.dashboard_color_code_dict["og_it"]["bg_color"]
							else:
								try:
									temp_bc = serve.OEE.dashboard_color_code_dict[f"dept_loss_{temp_what_id_i.wi_oed_m.dept_i.icode}"]["bg_color"]
								except:
									temp_bc = serve.OEE.dashboard_color_code_dict[f"dept_loss_{serve.Depts.PLE.icode}"]["bg_color"]
									a007_bw_logger.warning(f"what id mapping not found (wi_oed_m) ==> pl_id:{pl_id}, temp_what_id_i:{temp_what_id_i}")
							temp_list_al_bc.append(temp_bc)
							
						oee_dashboard_dict[pl_id]["m5al"]["x"] = temp_list_al_x
						oee_dashboard_dict[pl_id]["m5al"]["yn"] = temp_list_al_yn
						oee_dashboard_dict[pl_id]["m5al"]["bn"] = temp_list_al_bn
						oee_dashboard_dict[pl_id]["m5al"]["bc"] = temp_list_al_bc
						oee_dict[pl_id]["lu_m5al_list"] = copy.deepcopy(avl_loss_unique)
					# [Major 5 Availability Losses] - end

					# [Loss Time Analysis (waterfall)] - start
					captured_dt_distribution = []
					for dept in serve.OEE.depts_list:
						temp_what_id_list = oee_events_dic[dept.icode]
						idle_events_dept = idle_events_pl_upoe.filter(what_id_i__in = temp_what_id_list)
						temp_tit = idle_events_dept.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
						captured_dt_distribution.append({"dashboard_color_code_dict_key": f'dept_loss_{dept.icode}', "dept_desc":dept.description, "tit":temp_tit})
					
					idle_events_og = idle_events_pl.filter(what_id_i = None, where_id_i=None)
					if idle_events_og.exists():
						temp_tit = idle_events_og.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
						captured_dt_distribution.append({"dashboard_color_code_dict_key": "og_it", "dept_desc": wf_og_it_bar_xn, "tit":temp_tit})
					
					captured_dt_distribution_sorted = sorted(captured_dt_distribution, key=lambda x:x["tit"], reverse=True)
					temp_list_wf_xn = [wf_first_bar_xn]
					planned_prod_time_mins = serve.convert_float_with_int_possibility(planned_prod_time_secs/60, 1)
					temp_list_wf_bn = [planned_prod_time_mins]
					temp_str = f"{planned_prod_time_mins}Min"
					temp_list_wf_y = [[0,planned_prod_time_mins]]
					temp_list_wf_bc = [serve.OEE.dashboard_color_code_dict["plan_time"]["bg_color"]]
					if planned_prod_time_mins>1:
						temp_str = temp_str + "s"
					temp_list_wf_bntt = [temp_str+f"(100%)"]
					temp_avl_time = planned_prod_time
					for dept_dic in captured_dt_distribution_sorted:
						temp_list_wf_xn.append(dept_dic["dept_desc"])
						temp_avl_time_mins = serve.convert_float_with_int_possibility(temp_avl_time.total_seconds()/60, 1)
						temp_idle_time_mins = serve.convert_float_with_int_possibility(dept_dic["tit"].total_seconds()/60, 1)
						temp_list_wf_y.append([temp_avl_time_mins-temp_idle_time_mins, temp_avl_time_mins])
						temp_list_wf_bn.append(temp_idle_time_mins)
						temp_list_wf_bc.append(serve.OEE.dashboard_color_code_dict[dept_dic["dashboard_color_code_dict_key"]]["bg_color"])
						temp_str = f" {temp_idle_time_mins}Min"
						if temp_idle_time_mins>1:
							temp_str = temp_str + "s"
						temp_loss_per = serve.convert_float_with_int_possibility((dept_dic["tit"]/planned_prod_time)*100, 1)
						temp_list_wf_bntt.append(temp_str + f"({temp_loss_per}%)")
						temp_avl_time = temp_avl_time - dept_dic["tit"]
					temp_list_wf_xn.append(wf_last_bar_xn)
					operating_time_mins = serve.convert_float_with_int_possibility(operating_time_secs/60, 1)
					temp_list_wf_y.append([0,operating_time_mins])
					temp_list_wf_bn.append(operating_time_mins)
					temp_list_wf_bc.append(serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"])
					temp_str = f" {operating_time_mins}Min"
					if operating_time_mins>1:
						temp_str = temp_str + "s"
					temp_loss_per = round((operating_time/planned_prod_time)*100, 1)
					temp_list_wf_bntt.append(temp_str + f"({temp_loss_per}%)")
					oee_dashboard_dict[pl_id]["wf"]["xn"] = temp_list_wf_xn
					oee_dashboard_dict[pl_id]["wf"]["y"] = temp_list_wf_y
					oee_dashboard_dict[pl_id]["wf"]["bn"] = temp_list_wf_bn
					oee_dashboard_dict[pl_id]["wf"]["bntt"] = temp_list_wf_bntt
					oee_dashboard_dict[pl_id]["wf"]["bc"] = temp_list_wf_bc
					# [Loss Time Analysis (waterfall)] - end

					# [Time Bar] - start
					temp_list = []
					temp_total_ie = len(idle_events_pl)
					temp_event_end_time = temp_shift_start_dt
					for index_ie, ie in enumerate(idle_events_pl):
						bg_color = ""
						duration = ie.start_time - temp_event_end_time 
						temp_list.append({
							"width": f"{(duration/shift.duration_time)*100}%",
							"bg_color": serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], 
							"title": f"""
								<b> Start Time: </b> {serve.get_standard_str_format_of_dt_or_d(temp_event_end_time)}<br><br>
								<b> End Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.start_time)}<br><br>
								<b> {serve.OEE.dashboard_color_code_dict["no_loss"]["name"]} </b>
							""",
						})
						duration = ie.temp_end_time - ie.start_time 
						if not ie.what_id_i:  
							bg_color = serve.OEE.dashboard_color_code_dict["og_it"]["bg_color"]
							temp_list.append({
								"width": f"{(duration/shift.duration_time)*100}%",
								"bg_color": bg_color, 
								"title": f"""
									<b> Start Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.start_time)}<br><br>
									<b> End Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.temp_end_time)}<br><br>
									<b> Waiting for response </b>
								""",
							})
							continue
						elif ie.what_id_i in serve.OEE.planned_oee_events:  
							bg_color = serve.OEE.dashboard_color_code_dict["no_plan"]["bg_color"]
						else: 
							try:
								bg_color = serve.OEE.dashboard_color_code_dict[f"dept_loss_{ie.what_id_i.wi_oed_m.dept_i.icode}"]["bg_color"]
							except:
								bg_color = serve.OEE.dashboard_color_code_dict[f"dept_loss_{serve.Depts.PLE.icode}"]["bg_color"]
								a007_bw_logger.warning(f"what id mapping not found (wi_oed_m), {pl_id} {ie.what_id_i} ")
						temp_list.append({
							"width": f"{(duration/shift.duration_time)*100}%",
							"bg_color": bg_color, 
							"title": f"""
								<b> Start Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.start_time)}<br><br>
								<b> End Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.temp_end_time)}<br><br>
								<b> Where: </b> {ie.where_id_i.name}<br><br>
								<b> What: </b> {ie.what_id_i.name}<br><br>
							""",
						})
						temp_event_end_time = ie.temp_end_time
						if index_ie == temp_total_ie - 1:
							duration = current_dt - ie.temp_end_time
							if duration:
								temp_list.append({
									"width": f"{(duration/shift.duration_time)*100}%",
									"bg_color": serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], 
									"title": f"""
										<b> Start Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.temp_end_time)}<br><br>
										<b> End Time: </b> {serve.get_standard_str_format_of_dt_or_d(current_dt)}<br><br>
										<b> {serve.OEE.dashboard_color_code_dict["no_loss"]["name"]} </b>
									""",
								})
					oee_dashboard_dict[pl_id]["time_bar"] = temp_list
					# [Time Bar] - end

			pl_th_list = []
			for pl_id in oee_dashboard_dict:
				a007_cache.set(serve.Apps.A007OEEMonitoring.cache_key_of_oee_dashboard_dict, oee_dashboard_dict)
				th = serve.run_as_thread(update_production_line_data, args = (pl_id,))
				pl_th_list.append(th)
			for th in pl_th_list:
				th.join()
			if logged_flag:
				logged_flag = False
			time.sleep(0.5)
			end = time.perf_counter()
		except Exception as e:
			if not logged_flag:
				a007_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag = True
			time.sleep(serve.error_wait)


def get_dashboard_dict(line_id):
	return oee_dashboard_dict[line_id]


def get_dashboard_report_dict(pl_id_list, custom_date, shift):
	oee_dashboard_report_dict = {} 
	text_wrapper = textwrap.TextWrapper(width=m5al_text_wrap_len_in_dashboard) 
	wf_first_bar_xn = "Plan Time".strip().split()
	wf_last_bar_xn = "Avl. Time".strip().split()
	oee_events_dic = {}
	report_ns_start_dt = shift.ns_start_date_time(date=custom_date)
	temp_dt = report_ns_start_dt.strftime("%d-%b-%Y")
	temp_dst = " ".join([report_ns_start_dt.strftime("%A"), shift.name])
	for dept in serve.OEE.depts_list:
		oee_events_dic[dept.icode] = list(serve.get_oee_events(dept_i=dept).values_list("icode",flat=True))
	temp_hrly_xn = []
	temp_hourly_full_time_periods_list = []
	cur_hr_no = 1
	temp_shift_start_dt = shift.start_date_time(custom_date)
	temp_next_shift_start_dt = report_ns_start_dt 
	period_start = temp_shift_start_dt
	period_end = temp_shift_start_dt
	hourly_list = []
	date_set = set([])
	while period_end != temp_next_shift_start_dt:
		period_end = period_start + datetime.timedelta(hours=1)
		if period_end>temp_next_shift_start_dt:
			period_end = temp_next_shift_start_dt
		temp_hrly_xn.append([period_start.strftime(serve.format_of_hour), "-", period_end.strftime(serve.format_of_hour)])

		same_hour_pq_hp_dic = {}
		temp_hourly_full_time_periods_list.append([period_start, period_end])
		while period_start<period_end:
			if not period_start.date() in same_hour_pq_hp_dic:
				same_hour_pq_hp_dic[period_start.date()]=[]
				date_set.add(period_start.date())
			same_hour_pq_hp_dic[period_start.date()].append(f'pq_H{period_start.hour}P{int(period_start.minute/minutes_period)}')
			period_start = period_start + datetime.timedelta(minutes=minutes_period)
		hourly_list.append(same_hour_pq_hp_dic.copy())
		cur_hr_no = cur_hr_no + 1
		period_start = period_end
	total_avl_time = shift.duration_time
	temp_time_secs = int(total_avl_time.total_seconds())
	mins, secs = divmod(temp_time_secs, 60)
	hrs, mins = divmod(mins, 60)
	temp_tot_avl_str = ""
	if hrs:
		temp_tot_avl_str = f"{hrs}Hr"
		if hrs>1:
			temp_tot_avl_str = temp_tot_avl_str + "s"
	if mins:
		temp_tot_avl_str = temp_tot_avl_str + f" {mins}Min"
		if mins>1:
			temp_tot_avl_str = temp_tot_avl_str + "s"
	if secs:
		temp_tot_avl_str = temp_tot_avl_str + f" {secs}Sec"
		if secs>1:
			temp_tot_avl_str = temp_tot_avl_str + "s"
	idle_events = get_idle_events(custom_date=custom_date, shift=shift).annotate(idle_time=F("end_time") - F("start_time"))
	change_overs = get_change_overs(custom_date=custom_date, shift=shift).annotate(run_time=F("end_time") - F("start_time"))
	oee_month_data = OEEData.objects.filter(Q(date__lt=custom_date, date__month=custom_date.month, date__year=custom_date.year) | Q(date=custom_date, shift__in=shift.past_shift_list)).filter(~Q(shift=None))
	production_plan_month_data = ProductionPlan.objects.filter(Q(plan_date__lt=custom_date, plan_date__month=custom_date.month , plan_date__year=custom_date.year) | Q(plan_date=custom_date, shift__in=shift.past_shift_list+[shift.shift]))	
	hourly_time_periods_list = temp_hourly_full_time_periods_list
	production_data_of_dates = ProductionData.objects.filter(date__in=date_set)

	def update_production_line_data(pl_id):
		with semaphore:
			pq_actual = 0
			oee_dashboard_report_dict[pl_id]["dt"]= temp_dt
			oee_dashboard_report_dict[pl_id]["dst"]= temp_dst
			oee_dashboard_report_dict[pl_id]["tot_avl_t"] = temp_tot_avl_str
			idle_events_pl = idle_events.filter(production_line_i_id=pl_id)
			idle_events_pl_upoe = idle_events_pl.exclude(what_id_i_id__in=serve.OEE.planned_oee_events)
			idle_events_pl_updt = idle_events_pl_upoe.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
			idle_events_pl_poe = idle_events_pl.filter(what_id_i_id__in=serve.OEE.planned_oee_events)
			idle_events_pl_pdt = idle_events_pl_poe.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
			change_overs_pl = change_overs.filter(production_line_i_id=pl_id)

			# [Hourly Production & PQ Actual Calculation] - start
			for index_i, sh_pq_hp_dic in enumerate(hourly_list):
				pq = 0
				for date in sh_pq_hp_dic:
					pq_col_list = production_data_of_dates.filter(date=date, production_line_i_id=pl_id).values_list(*sh_pq_hp_dic[date]).first() or []
					pq = pq + sum(filter(None, pq_col_list))
				temp_str = f"{pq} No"
				if pq > 1:
					temp_str = temp_str + "s"
				oee_dashboard_report_dict[pl_id]["hrly"]["y"].append(pq)
				oee_dashboard_report_dict[pl_id]["hrly"]["bntt"].append(temp_str)
			pq_actual = sum(oee_dashboard_report_dict[pl_id]["hrly"]["y"])
			temp_pq_actual = pq_actual or 1
			temp_hrly_bar_counts = len(oee_dashboard_report_dict[pl_id]["hrly"]["t"])
			for index_htp, htp in enumerate(hourly_time_periods_list):
				if temp_hrly_bar_counts and index_htp < temp_hrly_bar_counts - 1 and last_co == idle_events_pl_poe_count:
					continue
				summation_h_co_ct = datetime.timedelta()
				if change_overs_pl.exists():
					co_hour_format = change_overs_pl.filter(start_time__lte = htp[1],end_time__gt = htp[0]).annotate(
						temp_h_start_time= Case(
							When(start_time__lt = htp[0], then = htp[0]), 
							default = F("start_time")
						),
						temp_h_end_time = Case(
							When(end_time__gt = htp[1], then = htp[1]), 
							default = F("end_time")
						),
						h_run_time = F("temp_h_end_time") - F("temp_h_start_time")
					)
					for hco in co_hour_format:
						pn_ct = serve.get_ct_of_pn_on_pl(part_number = hco.part_number_i, production_line = hco.production_line_i)
						summation_h_co_ct = summation_h_co_ct + hco.h_run_time*pn_ct
					h_avg_ct_pl = summation_h_co_ct/(htp[1]-htp[0])
				else:
					h_avg_ct_pl = serve.get_ct_of_pn_on_pl(production_line_id=pl_id)
				idle_events_pl_poe_h = idle_events_pl_poe.filter(start_time__lte = htp[1],end_time__gt = htp[0]).annotate(
					temp_h_start_time = Case(
						When(start_time__lt = htp[0], then = htp[0]), 
						default = F("start_time")
					),
					temp_h_end_time = Case(
						When(end_time__gt = htp[1], then = htp[1]), 
						default = F("end_time")
					),
					h_idle_time = F("temp_h_end_time") - F("temp_h_start_time")
				).aggregate(pdt = Sum('h_idle_time'))['pdt'] or datetime.timedelta()
				temp_hour_target = int((htp[1]-htp[0]-idle_events_pl_poe_h).total_seconds()/h_avg_ct_pl)
				temp_hour_actual = oee_dashboard_report_dict[pl_id]["hrly"]["y"][index_htp]
				if temp_hour_target:
					temp_hour_percent = serve.convert_float_with_int_possibility((temp_hour_actual/temp_hour_target)*100,1)
				else:
					temp_hour_percent = 100
				temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_hour_percent)
				temp_str = f"{temp_hour_target} No"
				if temp_hour_target > 1:
					temp_str = temp_str + "s"
				if len(oee_dashboard_report_dict[pl_id]["hrly"]["t"]) <= index_htp:
					oee_dashboard_report_dict[pl_id]["hrly"]["t"].append(temp_hour_target)
					oee_dashboard_report_dict[pl_id]["hrly"]["ltt"].append(f"{temp_str}, Adherence:{temp_hour_percent}%")
					oee_dashboard_report_dict[pl_id]["hrly"]["bc"].append(temp_bg_color)
					continue
				oee_dashboard_report_dict[pl_id]["hrly"]["t"][index_htp] = temp_hour_target
				oee_dashboard_report_dict[pl_id]["hrly"]["ltt"][index_htp] = f"{temp_str}, Adherence:{temp_hour_percent}%"
				oee_dashboard_report_dict[pl_id]["hrly"]["bc"][index_htp] = temp_bg_color
			# [Hourly Production & PQ Actual Calculation] - end

			# [Availability Calculation] - start
			temp_time_secs = int(idle_events_pl_pdt.total_seconds())
			mins, secs = divmod(temp_time_secs, 60)
			hrs, mins = divmod(mins, 60)
			temp_str = ""
			if not any([hrs, mins, secs]):
				temp_str = serve.na_str
			if hrs:
				temp_str = f"{hrs}Hr"
				if hrs > 1:
					temp_str = temp_str + "s"
			if mins:
				temp_str = temp_str + f" {mins}Min"
				if mins > 1:
					temp_str = temp_str + "s"
			if secs:
				temp_str = temp_str + f" {secs}Sec"
				if secs > 1:
					temp_str = temp_str + "s"
			oee_dashboard_report_dict[pl_id]["pdt"] = temp_str
			planned_prod_time = total_avl_time - idle_events_pl_pdt
			planned_prod_time_secs = round(planned_prod_time.total_seconds()) or 1
			if planned_prod_time_secs<60:
				temp_str = f"{planned_prod_time_secs}Sec"
				if planned_prod_time_secs>1:
					temp_str = temp_str + "s"
			else:
				planned_prod_time_mins = serve.convert_float_with_int_possibility(planned_prod_time_secs/60, 1)
				temp_str = f"{planned_prod_time_mins}Min"
				if planned_prod_time_mins>1:
					temp_str = temp_str + "s"
			oee_dashboard_report_dict[pl_id]["at_pl"]= temp_str
			operating_time = planned_prod_time - idle_events_pl_updt
			operating_time_secs = round(operating_time.total_seconds())
			if operating_time_secs<60:
				temp_str = f"{operating_time_secs}Sec"
				if operating_time_secs>1:
					temp_str = temp_str + "s"
			else:
				operating_time_mins = serve.convert_float_with_int_possibility(operating_time_secs/60, 1)
				temp_str = f" {operating_time_mins}Min"
				if operating_time_mins>1:
					temp_str = temp_str + "s"
			oee_dashboard_report_dict[pl_id]["at_ac"]= temp_str
			oee_avl = serve.convert_float_with_int_possibility((operating_time/planned_prod_time)*100, 1)
			oee_dashboard_report_dict[pl_id]["avl_p"]= oee_avl
			oee_dashboard_report_dict[pl_id]["avl_p_bc"], temp = serve.get_bg_txt_color_of_percent(oee_avl)
			oee_dashboard_report_dict[pl_id]["avl_ps"]= f"{oee_avl}%"
			avl_ls_secs = planned_prod_time_secs - operating_time_secs
			
			if avl_ls_secs:
				if avl_ls_secs < 60:
					temp_str = f"Loss: {avl_ls_secs}Sec"
					if avl_ls_secs>1:
						temp_str = temp_str + "s"
				else:
					avl_ls_mins = serve.convert_float_with_int_possibility(avl_ls_secs/60, 1)
					temp_str = f"Loss: {avl_ls_mins}Min"
					if avl_ls_mins>1:
						temp_str = temp_str + "s"
				temp_bc, temp_tc = serve.loss_bg_color, serve.loss_txt_color
			else:
				temp_str = serve.OEE.dashboard_color_code_dict["no_loss"]["name"]
				temp_bc, temp_tc = serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], serve.OEE.dashboard_color_code_dict["no_loss"]["txt_color"]
			oee_dashboard_report_dict[pl_id]["avl_ls"] = temp_str
			oee_dashboard_report_dict[pl_id]["avl_ls_bc"] = temp_bc
			oee_dashboard_report_dict[pl_id]["avl_ls_tc"] = temp_tc
			# [Availability Calculation] - end

			# [Performance Calculation] - start
			summation_co_ct = datetime.timedelta()
			temp_dic = {}
			oee_dashboard_report_dict[pl_id]["psut_tc"] = change_overs_pl.count()
			for co in change_overs_pl:
				if co.part_number_i:
					pno = co.part_number_i.name
				else:
					pno = co.temp_pn
				temp_pq = co.pq
				if pno in temp_dic:
					temp_dic[pno] = temp_dic[pno] + f' | {temp_pq} ({co.start_time.strftime("%I:%M%p")} - {co.end_time.strftime("%I:%M%p")})'
				else:
					temp_dic[pno] = f'{temp_pq} ({co.start_time.strftime("%I:%M%p")} - {co.end_time.strftime("%I:%M%p")})'

				pn_ct = serve.get_ct_of_pn_on_pl(part_number=co.part_number_i, production_line=co.production_line_i)
				co_start_time = co.start_time
				co_end_time = co.end_time
				
				idle_events_pl_poe_co = idle_events_pl_poe.filter(start_time__lte=co_end_time, end_time__gt=co_start_time).annotate(
					temp_co_start_time= Case(
						When(start_time__lt=co_start_time, then=co_start_time), 
						default=F("start_time")
					),
					temp_co_end_time = Case(
						When(end_time__gt=co_end_time, then=co_end_time), 
						default=F("end_time")
					)
				).annotate(co_idle_time=F("temp_co_end_time") - F("temp_co_start_time")).aggregate(pdt = Sum('co_idle_time'))['pdt'] or datetime.timedelta()
				summation_co_ct = summation_co_ct + (co.run_time - idle_events_pl_poe_co)*pn_ct
			temp_list = []
			for index_i, i in enumerate(temp_dic):
				temp_list.append(": ".join([f'{index_i+1}) {i}', str(temp_dic[i]).lower()]))
			oee_dashboard_report_dict[pl_id]["psut_data"] = "\n".join(temp_list)

			avg_ct_pl = summation_co_ct/planned_prod_time or serve.get_ct_of_pn_on_pl(production_line_id=pl_id)
			temp_avg_ct_pl = serve.convert_float_with_int_possibility(avg_ct_pl, 1)
			temp_str = f"{temp_avg_ct_pl}Sec"
			if temp_avg_ct_pl>1:
				temp_str = temp_str + "s"
			oee_dashboard_report_dict[pl_id]["avg_ct"] = temp_str
			pq_perf_plan = int(operating_time_secs//avg_ct_pl)
			oee_dashboard_report_dict[pl_id]["pt_pp"] = pq_perf_plan
			oee_dashboard_report_dict[pl_id]["pt_pa"] = pq_actual
			
			temp_pq_perf_plan = pq_perf_plan or 1
			oee_perf = serve.convert_float_with_int_possibility((pq_actual/temp_pq_perf_plan)*100,1)
			if not pq_perf_plan:
				oee_perf = 100
			temp_str = f"{oee_perf}%"
			if oee_perf>100:
				oee_perf = 100
				temp_str = f">{oee_perf}%"
			oee_dashboard_report_dict[pl_id]["perf_p"] = oee_perf
			oee_dashboard_report_dict[pl_id]["perf_p_bc"], temp = serve.get_bg_txt_color_of_percent(oee_perf)
			oee_dashboard_report_dict[pl_id]["perf_ps"] = temp_str
			temp_loss_qty = pq_perf_plan - pq_actual
			perf_ls = temp_loss_qty if temp_loss_qty >= 0 else 0
			if perf_ls:
				temp_str = f"Loss: {perf_ls} No"
				if perf_ls > 1:
					temp_str = temp_str + "s"
				temp_bc, temp_tc = serve.loss_bg_color, serve.loss_txt_color
			else:
				temp_str = serve.OEE.dashboard_color_code_dict["no_loss"]["name"]
				temp_bc, temp_tc = serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], serve.OEE.dashboard_color_code_dict["no_loss"]["txt_color"]
			oee_dashboard_report_dict[pl_id]["perf_ls"] = temp_str
			oee_dashboard_report_dict[pl_id]["perf_ls_bc"] = temp_bc
			oee_dashboard_report_dict[pl_id]["perf_ls_tc"] = temp_tc
			# [Performance Calculation] - end

			# [Quality Calculation] - start
			rej_c = RejectionReworkEntryData.objects.filter(booked_datetime__gte = temp_shift_start_dt,
				booked_datetime__lt = temp_next_shift_start_dt,
				production_line_i =  pl_id,
				part_status_i = serve.Others.rejected_part
			).count()
			rew_c = RejectionReworkEntryData.objects.filter(booked_datetime__gte = temp_shift_start_dt,
				booked_datetime__lt = temp_next_shift_start_dt,
				production_line_i =  pl_id,
				part_status_i = serve.Others.rework_in_progress
			).count()
			oee_dashboard_report_dict[pl_id]["qt_rej_rew"] = rej_c + rew_c
			pq_ok_p = pq_actual - rej_c - rew_c
			oee_dashboard_report_dict[pl_id]["qt_okp"] = pq_ok_p
			qa_ls = rej_c + rew_c
			if qa_ls:
				temp_str = f"Loss: {qa_ls} No"
				if qa_ls > 1:
					temp_str = temp_str + "s"
				temp_bc, temp_tc = serve.loss_bg_color, serve.loss_txt_color
			else:
				temp_str = serve.OEE.dashboard_color_code_dict["no_loss"]["name"]
				temp_bc, temp_tc = serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], serve.OEE.dashboard_color_code_dict["no_loss"]["txt_color"]
			oee_dashboard_report_dict[pl_id]["qa_ls"] = temp_str
			oee_dashboard_report_dict[pl_id]["qa_ls_bc"] = temp_bc
			oee_dashboard_report_dict[pl_id]["qa_ls_tc"] = temp_tc
			oee_qa = serve.convert_float_with_int_possibility((pq_ok_p/temp_pq_actual)*100, 1)
			if not pq_actual:
				oee_qa = 0
			oee_dashboard_report_dict[pl_id]["qa_p"] = oee_qa
			oee_dashboard_report_dict[pl_id]["qa_p_bc"], temp = serve.get_bg_txt_color_of_percent(oee_qa)
			oee_dashboard_report_dict[pl_id]["qa_ps"] = f"{oee_qa}%"
			# [Quality Calculation] - end

			# [OEE Calculation] - start
			oee = serve.convert_float_with_int_possibility((operating_time/planned_prod_time)*\
				(pq_actual/temp_pq_perf_plan)*\
				(oee_dashboard_report_dict[pl_id]["qt_okp"]/temp_pq_actual)*100, 1)
			temp_str = f"{oee}%"
			if oee>100:
				oee = 100
				temp_str = f">{oee}%"
			oee_dashboard_report_dict[pl_id]["oee_p"] = oee
			oee_dashboard_report_dict[pl_id]["oee_p_bc"], temp = serve.get_bg_txt_color_of_percent(oee)
			oee_dashboard_report_dict[pl_id]["oee_ps"] = temp_str
			oee_ps = temp_str
			# [OEE Calculation] - end

			# [Cumulative Data] - start
			oee_month_data_pl = oee_month_data.filter(production_line_i_id=pl_id)
			oee_month_data_pl_dic = {
				"tot_at": 0,
				"tot_pdt": 0,
				"tot_updt": 0,
				"tot_pq_plan": 0,
				"tot_pq_perf_plan": 0,
				"tot_pq_actual": 0,
				"tot_pq_ok_p": 0
			}
			oee_day_data_pl = oee_month_data_pl.filter(date=custom_date)
			oee_day_data_pl_dic = {
				"tot_at": 0,
				"tot_pdt": 0,
				"tot_updt": 0,
				"tot_pq_plan": 0,
				"tot_pq_perf_plan": 0,
				"tot_pq_actual": 0,
				"tot_pq_ok_p": 0
			}
			production_plan_month_data_pl = production_plan_month_data.filter(production_line_i_id=pl_id)
			last_revision = production_plan_month_data_pl.aggregate(last_revision = Max("revision"))["last_revision"]
			production_plan_month_data_pl_lr = production_plan_month_data_pl.filter(revision=last_revision)      
			production_plan_day_data_pl_lr = production_plan_month_data_pl_lr.filter(plan_date=custom_date)      
			production_plan_shift_data_pl_lr = production_plan_day_data_pl_lr.filter(shift=shift.shift)      
			oee_dashboard_report_dict[pl_id]["ct_s_ot"] = oee_ps
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(oee)
			oee_dashboard_report_dict[pl_id]["ct_s_obc"] = temp_bg_color
			oee_dashboard_report_dict[pl_id]["ct_s_otc"] = temp_txt_color
			pq_plan = int(planned_prod_time_secs//avg_ct_pl)
			temp_ct_plan, temp_actual = pq_plan, pq_actual
			oee_dashboard_report_dict[pl_id]["ct_s_ct_pl"] = serve.get_number_with_comma(temp_ct_plan)
			oee_dashboard_report_dict[pl_id]["ct_s_at"] = serve.get_number_with_comma(temp_actual)
			if temp_ct_plan:
				temp_percent = (temp_actual/temp_ct_plan)*100
			else:
				temp_percent = 100
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_percent)
			oee_dashboard_report_dict[pl_id]["ct_s_abc"] = temp_bg_color
			oee_dashboard_report_dict[pl_id]["ct_s_atc"] = temp_txt_color
			temp_ppc_plan = 0
			if production_plan_shift_data_pl_lr.exists():
				temp_ppc_plan = production_plan_shift_data_pl_lr.last().planned_qty
			oee_dashboard_report_dict[pl_id]["ct_s_ppc_pl"] = serve.get_number_with_comma(temp_ppc_plan)
			
			if oee_day_data_pl.exists():
				oee_day_data_pl_dic = oee_day_data_pl.aggregate(
					tot_at = Sum("avl_time"),
					tot_pdt = Sum("pdt"),
					tot_updt = Sum("updt"),
					tot_pq_plan = Sum("pq_plan"),
					tot_pq_perf_plan = Sum("pq_perf_plan"),
					tot_pq_actual = Sum("pq_actual"),
					tot_pq_ok_p = Sum("pq_ok_p"),
				)
			planned_prod_time_secs_d = oee_day_data_pl_dic["tot_at"] - oee_day_data_pl_dic["tot_pdt"] + planned_prod_time_secs
			operating_time_secs_d = planned_prod_time_secs_d - oee_day_data_pl_dic["tot_updt"] - idle_events_pl_updt.total_seconds()
			oee_avl_d = operating_time_secs_d/planned_prod_time_secs_d
			oee_perf_d = (oee_day_data_pl_dic["tot_pq_actual"] + pq_actual)/(oee_day_data_pl_dic["tot_pq_perf_plan"] + temp_pq_perf_plan)
			oee_qa_d = (oee_day_data_pl_dic["tot_pq_ok_p"] + pq_ok_p)/(oee_day_data_pl_dic["tot_pq_actual"] + temp_pq_actual)
			oee_d = serve.convert_float_with_int_possibility(oee_avl_d*oee_perf_d*oee_qa_d*100, 1)
			temp_str = f"{oee_d}%"
			if oee_d > 100:
				oee_d = 100
				temp_str = f">{oee_d}%"
			oee_dashboard_report_dict[pl_id]["ct_d_ot"] = temp_str
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(oee_d)
			oee_dashboard_report_dict[pl_id]["ct_d_obc"] = temp_bg_color
			oee_dashboard_report_dict[pl_id]["ct_d_otc"] = temp_txt_color
			temp_ct_plan, temp_actual = oee_day_data_pl_dic["tot_pq_plan"] + pq_plan, oee_day_data_pl_dic["tot_pq_actual"] + pq_actual
			oee_dashboard_report_dict[pl_id]["ct_d_ct_pl"] = serve.get_number_with_comma(temp_ct_plan)
			oee_dashboard_report_dict[pl_id]["ct_d_at"] = serve.get_number_with_comma(temp_actual)
			if temp_ct_plan:
				temp_percent = (temp_actual/temp_ct_plan)*100
			else:
				temp_percent = 100
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_percent)
			oee_dashboard_report_dict[pl_id]["ct_d_abc"] = temp_bg_color
			oee_dashboard_report_dict[pl_id]["ct_d_atc"] = temp_txt_color
			temp_ppc_plan = 0
			if production_plan_day_data_pl_lr.exists():
				temp_ppc_plan = production_plan_day_data_pl_lr.aggregate(tot_planned_qty = Coalesce(Sum("planned_qty"),0))["tot_planned_qty"]
			oee_dashboard_report_dict[pl_id]["ct_d_ppc_pl"] = serve.get_number_with_comma(temp_ppc_plan)

			if oee_month_data_pl.exists():
				oee_month_data_pl_dic = oee_month_data_pl.aggregate(
					tot_at = Sum("avl_time"),
					tot_pdt = Sum("pdt"),
					tot_updt = Sum("updt"),
					tot_pq_plan = Sum("pq_plan"),
					tot_pq_perf_plan = Sum("pq_perf_plan"),
					tot_pq_actual = Sum("pq_actual"),
					tot_pq_ok_p = Sum("pq_ok_p"),
				)

			planned_prod_time_secs_m = oee_month_data_pl_dic["tot_at"] - oee_month_data_pl_dic["tot_pdt"] + planned_prod_time_secs
			operating_time_secs_m = planned_prod_time_secs_m - oee_month_data_pl_dic["tot_updt"] - idle_events_pl_updt.total_seconds()
			oee_avl_m = operating_time_secs_m/planned_prod_time_secs_m
			oee_perf_m = (oee_month_data_pl_dic["tot_pq_actual"] + pq_actual)/(oee_month_data_pl_dic["tot_pq_perf_plan"] + temp_pq_perf_plan)
			oee_qa_m = (oee_month_data_pl_dic["tot_pq_ok_p"] + pq_ok_p)/(oee_month_data_pl_dic["tot_pq_actual"] + temp_pq_actual)
			oee_m = serve.convert_float_with_int_possibility(oee_avl_m*oee_perf_m*oee_qa_m*100, 1)
			temp_str = f"{oee_m}%"
			if oee_m > 100:
				oee_m = 100
				temp_str = f">{oee_m}%"
			oee_dashboard_report_dict[pl_id]["ct_m_ot"] = temp_str
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(oee_m)
			oee_dashboard_report_dict[pl_id]["ct_m_obc"] = temp_bg_color
			oee_dashboard_report_dict[pl_id]["ct_m_otc"] = temp_txt_color
			temp_ct_plan, temp_actual = oee_month_data_pl_dic["tot_pq_plan"] + pq_plan, oee_month_data_pl_dic["tot_pq_actual"] + pq_actual
			oee_dashboard_report_dict[pl_id]["ct_m_ct_pl"] = serve.get_number_with_comma(temp_ct_plan)
			oee_dashboard_report_dict[pl_id]["ct_m_at"] = serve.get_number_with_comma(temp_actual)
			if temp_ct_plan:
				temp_percent = (temp_actual/temp_ct_plan)*100
			else:
				temp_percent = 100
			temp_bg_color, temp_txt_color = serve.get_bg_txt_color_of_percent(temp_percent)
			oee_dashboard_report_dict[pl_id]["ct_m_abc"] = temp_bg_color
			oee_dashboard_report_dict[pl_id]["ct_m_atc"] = temp_txt_color
			temp_ppc_plan = 0
			if production_plan_month_data_pl_lr.exists():
				temp_ppc_plan = production_plan_month_data_pl_lr.aggregate(tot_planned_qty = Coalesce(Sum("planned_qty"),0))["tot_planned_qty"]
			oee_dashboard_report_dict[pl_id]["ct_m_ppc_pl"] = serve.get_number_with_comma(temp_ppc_plan)
			# [Cumulative Data] - end

			# [Major 5 Availability Losses] - start
			avl_loss_unique = list(idle_events_pl_upoe.values("what_id_i_id", "where_id_i_id").distinct())
			for avl_loss in avl_loss_unique:
				avl_loss["idle_time_al"]=idle_events_pl.filter(**avl_loss).aggregate(idle_time_al= Sum("idle_time"))["idle_time_al"] or datetime.timedelta()
			temp_list_al_x = []
			temp_list_al_yn = []
			temp_list_al_bn = []
			temp_list_al_bc = []
			for avl_loss in sorted(avl_loss_unique, key=lambda x:x["idle_time_al"], reverse=True)[:5]:
				temp_list = []
				it = serve.convert_float_with_int_possibility(avl_loss["idle_time_al"].total_seconds()/60,1)
				if avl_loss["where_id_i_id"]!=pl_id:
					temp_list.append(serve.get_icode_object(avl_loss["where_id_i_id"]).name)
				temp_what_id_i = serve.get_icode_object(avl_loss["what_id_i_id"])
				temp_list.append(temp_what_id_i.name) 
				temp_list_al_x.append(it)
				temp_list_al_yn.append(text_wrapper.fill(" - ".join(temp_list)).strip().splitlines())
				temp_list_al_bn.append(f"{it}Mins")
				temp_bc = ""
				if temp_what_id_i.icode in [serve.OEE.ongoing_idletime.icode, serve.OEE.uncaptured_event]:
					temp_bc = serve.OEE.dashboard_color_code_dict["og_it"]["bg_color"]
				else:
					try:
						temp_bc = serve.OEE.dashboard_color_code_dict[f"dept_loss_{temp_what_id_i.wi_oed_m.dept_i.icode}"]["bg_color"]
					except:
						temp_bc = serve.OEE.dashboard_color_code_dict[f"dept_loss_{serve.Depts.PLE.icode}"]["bg_color"]
						a007_bw_logger.warning(f"what id mapping not found (wi_oed_m) ==> pl_id:{pl_id}, temp_what_id_i:{temp_what_id_i}")
				temp_list_al_bc.append(temp_bc)
				
			oee_dashboard_report_dict[pl_id]["m5al"]["x"] = temp_list_al_x
			oee_dashboard_report_dict[pl_id]["m5al"]["yn"] = temp_list_al_yn
			oee_dashboard_report_dict[pl_id]["m5al"]["bn"] = temp_list_al_bn
			oee_dashboard_report_dict[pl_id]["m5al"]["bc"] = temp_list_al_bc
			# [Major 5 Availability Losses] - end

			# [Loss Time Analysis (waterfall)] - start
			captured_dt_distribution = []
			for dept in serve.OEE.depts_list:
				temp_what_id_list = oee_events_dic[dept.icode]
				idle_events_dept = idle_events_pl_upoe.filter(what_id_i__in = temp_what_id_list)
				temp_tit = idle_events_dept.aggregate(tit=Sum("idle_time"))["tit"] or datetime.timedelta()
				captured_dt_distribution.append({"dashboard_color_code_dict_key": f'dept_loss_{dept.icode}', "dept_desc":dept.description, "tit":temp_tit})
			
			
			captured_dt_distribution_sorted = sorted(captured_dt_distribution, key=lambda x:x["tit"], reverse=True)
			temp_list_wf_xn = [wf_first_bar_xn]
			planned_prod_time_mins = serve.convert_float_with_int_possibility(planned_prod_time_secs/60, 1)
			temp_list_wf_bn = [planned_prod_time_mins]
			temp_str = f"{planned_prod_time_mins}Min"
			temp_list_wf_y = [[0,planned_prod_time_mins]]
			temp_list_wf_bc = [serve.OEE.dashboard_color_code_dict["plan_time"]["bg_color"]]
			if planned_prod_time_mins>1:
				temp_str = temp_str + "s"
			temp_list_wf_bntt = [temp_str+f"(100%)"]
			temp_avl_time = planned_prod_time
			for dept_dic in captured_dt_distribution_sorted:
				temp_list_wf_xn.append(dept_dic["dept_desc"])
				temp_avl_time_mins = serve.convert_float_with_int_possibility(temp_avl_time.total_seconds()/60, 1)
				temp_idle_time_mins = serve.convert_float_with_int_possibility(dept_dic["tit"].total_seconds()/60, 1)
				temp_list_wf_y.append([temp_avl_time_mins-temp_idle_time_mins, temp_avl_time_mins])
				temp_list_wf_bn.append(temp_idle_time_mins)
				temp_list_wf_bc.append(serve.OEE.dashboard_color_code_dict[dept_dic["dashboard_color_code_dict_key"]]["bg_color"])
				temp_str = f" {temp_idle_time_mins}Min"
				if temp_idle_time_mins>1:
					temp_str = temp_str + "s"
				temp_loss_per = serve.convert_float_with_int_possibility((dept_dic["tit"]/planned_prod_time)*100, 1)
				temp_list_wf_bntt.append(temp_str + f"({temp_loss_per}%)")
				temp_avl_time = temp_avl_time - dept_dic["tit"]
			temp_list_wf_xn.append(wf_last_bar_xn)
			operating_time_mins = serve.convert_float_with_int_possibility(operating_time_secs/60, 1)
			temp_list_wf_y.append([0,operating_time_mins])
			temp_list_wf_bn.append(operating_time_mins)
			temp_list_wf_bc.append(serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"])
			temp_str = f" {operating_time_mins}Min"
			if operating_time_mins>1:
				temp_str = temp_str + "s"
			temp_loss_per = round((operating_time/planned_prod_time)*100, 1)
			temp_list_wf_bntt.append(temp_str + f"({temp_loss_per}%)")
			oee_dashboard_report_dict[pl_id]["wf"]["xn"] = temp_list_wf_xn
			oee_dashboard_report_dict[pl_id]["wf"]["y"] = temp_list_wf_y
			oee_dashboard_report_dict[pl_id]["wf"]["bn"] = temp_list_wf_bn
			oee_dashboard_report_dict[pl_id]["wf"]["bntt"] = temp_list_wf_bntt
			oee_dashboard_report_dict[pl_id]["wf"]["bc"] = temp_list_wf_bc
			# [Loss Time Analysis (waterfall)] - end

			# [Time Bar] - start
			temp_list = []
			temp_total_ie = len(idle_events_pl)
			temp_event_end_time = temp_shift_start_dt
			for index_ie, ie in enumerate(idle_events_pl):
				bg_color = ""
				duration = ie.start_time - temp_event_end_time 
				temp_list.append({
					"width": f"{(duration/shift.duration_time)*100}%",
					"bg_color": serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], 
					"title": f"""
						<b> Start Time: </b> {serve.get_standard_str_format_of_dt_or_d(temp_event_end_time)}<br><br>
						<b> End Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.start_time)}<br><br>
						<b> {serve.OEE.dashboard_color_code_dict["no_loss"]["name"]} </b>
					""",
				})
				duration = ie.end_time - ie.start_time 
				if not ie.what_id_i:  
					bg_color = serve.OEE.dashboard_color_code_dict["og_it"]["bg_color"]
					temp_list.append({
						"width": f"{(duration/shift.duration_time)*100}%",
						"bg_color": bg_color, 
						"title": f"""
							<b> Start Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.start_time)}<br><br>
							<b> End Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.end_time)}<br><br>
							<b> Waiting for response </b>
						""",
					})
					continue
				elif ie.what_id_i in serve.OEE.planned_oee_events:  
					bg_color = serve.OEE.dashboard_color_code_dict["no_plan"]["bg_color"]
				else: 
					try:
						bg_color = serve.OEE.dashboard_color_code_dict[f"dept_loss_{ie.what_id_i.wi_oed_m.dept_i.icode}"]["bg_color"]
					except:
						bg_color = serve.OEE.dashboard_color_code_dict[f"dept_loss_{serve.Depts.PLE.icode}"]["bg_color"]
						a007_bw_logger.warning(f"what id mapping not found (wi_oed_m), {pl_id} {ie.what_id_i} ")
				temp_list.append({
					"width": f"{(duration/shift.duration_time)*100}%",
					"bg_color": bg_color, 
					"title": f"""
						<b> Start Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.start_time)}<br><br>
						<b> End Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.end_time)}<br><br>
						<b> Where: </b> {ie.where_id_i.name}<br><br>
						<b> What: </b> {ie.what_id_i.name}<br><br>
					""",
				})
				temp_event_end_time = ie.end_time
				if index_ie == temp_total_ie - 1:
					duration = report_ns_start_dt - ie.end_time
					if duration:
						temp_list.append({
							"width": f"{(duration/shift.duration_time)*100}%",
							"bg_color": serve.OEE.dashboard_color_code_dict["no_loss"]["bg_color"], 
							"title": f"""
								<b> Start Time: </b> {serve.get_standard_str_format_of_dt_or_d(ie.end_time)}<br><br>
								<b> End Time: </b> {serve.get_standard_str_format_of_dt_or_d(report_ns_start_dt)}<br><br>
								<b> {serve.OEE.dashboard_color_code_dict["no_loss"]["name"]} </b>
							""",
						})
			oee_dashboard_report_dict[pl_id]["time_bar"] = temp_list
			# [Time Bar] - end
		  
	for pl_id in pl_id_list:
		pl = serve.get_icode_object(pl_id)
		oee_dashboard_report_dict[pl_id] = copy.deepcopy(sub_oee_dashboard_report_dict_default)
		oee_dashboard_report_dict[pl_id]["pl_n"] = pl.name
		pls = pl.opls_pl
		oee_dashboard_report_dict[pl_id]["pl_bg_c"] = pls.pl_grp_cl_bg
		oee_dashboard_report_dict[pl_id]["pl_txt_c"] = pls.pl_grp_cl_txt
		oee_dashboard_report_dict[pl_id]["hrly"]["xn"] = temp_hrly_xn
		update_production_line_data(pl_id)
	return oee_dashboard_report_dict


serve.run_as_thread(routine_work)


try:
	current_dt = current_time_datetime
	change_overs = get_change_overs(custom_date=serve.get_custom_shift_date(current_dt), shift=serve.get_shift(current_dt))
	shift = serve.get_shift(current_dt)
	custom_date = serve.get_custom_shift_date(current_dt)
	temp_shift_start_dt = shift.start_date_time(custom_date)
	same_day_pq_hp_list = []
	end_hour = current_dt.hour
	end_hour_minute = current_dt.minute
	for hour in range(0, end_hour):
		for j in range(max_minute_period):
			same_day_pq_hp_list.append(f'pq_H{hour}P{j}')
	for p in range(int(end_hour_minute/minutes_period)):
		same_day_pq_hp_list.append(f'pq_H{end_hour}P{p}')
	phi = pq_hp_index
	idle_events = get_idle_events(custom_date=custom_date, shift=shift).filter(end_time = None)
	for ie in idle_events:
		if not ie.what_id_i:
			ie.what_id_i = serve.OEE.server_restart_event
			ie.where_id_i = ie.production_line_i
		ie.end_time = current_dt
		ie.save()
	for pl in serve.get_production_lines_of_oee_enabled():
		pl_id = pl.icode
		oee_dict[pl_id] = sub_dict_default.copy()
		oee_dashboard_dict[pl_id] = copy.deepcopy(sub_oee_dashboard_dict_default)
		oee_dashboard_dict[pl_id]["pl_n"] = pl.name
		pls = pl.opls_pl
		oee_dict[pl_id]["where_id_ps"] = pls.production_station_i.icode
		oee_ps_pl_dict[pls.production_station_i.icode] = pl_id
		oee_dict[pl_id]["pl_bg_c"] = pls.pl_grp_cl_bg
		oee_dashboard_dict[pl_id]["pl_bg_c"] = pls.pl_grp_cl_bg
		oee_dict[pl_id]["pl_txt_c"] = pls.pl_grp_cl_txt
		oee_dashboard_dict[pl_id]["pl_txt_c"] = pls.pl_grp_cl_txt
		oee_dashboard_dict[pl_id]["slide_timeout"] = pls.dashboard_ht
		oee_dict[pl_id]["pq_hp_i"] = phi
		pq_data = ProductionData.objects.filter(date=current_dt.date(), production_line_i=pl)
		pq_col_list = pq_data.values_list(*same_day_pq_hp_list).first() or []
		pq = sum(filter(None, pq_col_list))
		oee_dict[pl_id]["opq"] = pq
		change_overs_pl = change_overs.filter(production_line_i_id=pl_id)
		if change_overs_pl.exists():
			temp_tpq = change_overs_pl.aggregate(tpq=Sum('pq'))["tpq"] or 0
			oee_dict[pl_id]["spq"] = temp_tpq
			oee_dict[pl_id]["spq_upto_lcho"] = temp_tpq
			last_co = change_overs_pl.latest("start_time")
			oee_dict[pl_id]["rpn"] = last_co.temp_pn or last_co.part_number_i.name
			oee_dict[pl_id]["rpn_i"] = None if last_co.temp_pn else last_co.part_number_i
			oee_dict[pl_id]["rpn_ct"] = serve.get_ct_of_pn_on_pl(part_number=last_co.part_number_i, production_line_id=pl_id)
			oee_dict[pl_id]["last_chg_ov_t"] = last_co.end_time or last_co.start_time
		else:
			oee_dict[pl_id]["spq"] = 0
			oee_dict[pl_id]["spq_upto_lcho"] = 0
			oee_dict[pl_id]["rpn_ct"] = serve.get_ct_of_pn_on_pl(production_line_id=pl_id)
			oee_dict[pl_id]["last_chg_ov_t"] = temp_shift_start_dt
		a007_cache.set(serve.Apps.A007OEEMonitoring.cache_key_of_oee_dict, oee_dict)
		serve.run_as_thread(prod_data_generator, args = (pl_id,))
		serve.run_as_thread(
			idle_time_monitor,
			args = (
				pls.production_line_i_id,
				pls.ie_min_to_reg_m*60,
				pls.ie_l1_es_m*60,
				pls.ie_l2_es_m*60,
				pls.ie_l3_es_m*60,
			)
		)
		a007_bw_logger.info(f"{serve.an_oee_monitoring}: {pl.icode} was started")
except Exception as e:
	a007_bw_logger.error("Exception occurred", exc_info=True)

semaphore = Semaphore(serve.a007_max_no_of_lines_in_update_dashboard_dict)

if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
	# # serve.run_as_thread(data_decode)
	# # serve.run_as_thread(data_encode)
	# serve.run_as_thread(move_prod_data)
	# serve.run_as_thread(oee_eve_handler)
	serve.run_as_thread(change_overs_handler)
	serve.run_as_thread(google_chat_hrly_prod)
	# serve.run_as_thread(google_chat_oee_eve)
	# # serve.run_as_thread(google_chat_prod_ch_ov)
	# # serve.run_as_thread(google_chat_manu_com)
	# # serve.run_as_thread(google_chat_test_oee_eve_id)
	serve.run_as_thread(update_dashboard_dict)
	schedule.every().day.at(serve.Shifts.ShiftA.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.Shifts.ShiftB.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.Shifts.ShiftC.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,production_day_summary_report_mail,)
	# schedule.every().day.at(serve.OEE.ShiftA.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftA)
	# schedule.every().day.at(serve.OEE.ShiftB.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftB)
	# schedule.every().day.at(serve.OEE.ShiftC.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftC)
	# schedule.every().day.at(serve.OEE.ShiftC.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, )
	# schedule.every().day.at(serve.OEE.ShiftA.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	# schedule.every().day.at(serve.OEE.ShiftB.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	# schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	# schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail,)
	# # schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail,)
	# # schedule.every().day.at(serve.OEE.day_ml_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,major_loss_events_of_day_mail,)
	# # schedule.every().day.at(serve.OEE.day_pn_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,part_number_mail,)
	# schedule.every().day.at(serve.OEE.day_plan_vs_actual_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,production_plan_vs_actual_mail,)
	# # schedule.every().day.at(serve.OEE.ShiftA.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftA,))
	# # schedule.every().day.at(serve.OEE.ShiftB.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftB,))
	# # schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftC,))
	# # schedule.every().day.at(serve.OEE.ShiftA.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftA,))
	# # schedule.every().day.at(serve.OEE.ShiftB.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftB,))
	# # schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftC,))

elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
	serve.run_as_thread(data_decode)
	serve.run_as_thread(data_encode)
	serve.run_as_thread(move_prod_data)
	serve.run_as_thread(oee_eve_handler)
	serve.run_as_thread(change_overs_handler)
	serve.run_as_thread(google_chat_hrly_prod)
	serve.run_as_thread(google_chat_oee_eve)
	serve.run_as_thread(google_chat_prod_ch_ov)
	serve.run_as_thread(google_chat_manu_com)
	serve.run_as_thread(google_chat_test_oee_eve_id)
	serve.run_as_thread(update_dashboard_dict)
	schedule.every().day.at(serve.Shifts.ShiftA.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.Shifts.ShiftB.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.Shifts.ShiftC.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.OEE.ShiftA.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftA)
	schedule.every().day.at(serve.OEE.ShiftB.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftB)
	schedule.every().day.at(serve.OEE.ShiftC.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftC)
	schedule.every().day.at(serve.OEE.ShiftC.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, )
	schedule.every().day.at(serve.OEE.ShiftA.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	schedule.every().day.at(serve.OEE.ShiftB.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail,)
	schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,production_day_summary_report_mail,)
	# schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail,)
	# schedule.every().day.at(serve.OEE.day_ml_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,major_loss_events_of_day_mail,)
	# schedule.every().day.at(serve.OEE.day_pn_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,part_number_mail,)
	schedule.every().day.at(serve.OEE.day_plan_vs_actual_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,production_plan_vs_actual_mail,)
	# schedule.every().day.at(serve.OEE.ShiftA.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftA,))
	# schedule.every().day.at(serve.OEE.ShiftB.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftB,))
	# schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftC,))
	# schedule.every().day.at(serve.OEE.ShiftA.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftA,))
	# schedule.every().day.at(serve.OEE.ShiftB.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftB,))
	# schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftC,))

elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
	serve.run_as_thread(data_decode)
	serve.run_as_thread(data_encode)
	serve.run_as_thread(move_prod_data)
	serve.run_as_thread(oee_eve_handler)
	serve.run_as_thread(change_overs_handler)
	serve.run_as_thread(google_chat_hrly_prod)
	serve.run_as_thread(google_chat_oee_eve)
	serve.run_as_thread(google_chat_prod_ch_ov)
	serve.run_as_thread(google_chat_manu_com)
	serve.run_as_thread(google_chat_test_oee_eve_id)
	serve.run_as_thread(update_dashboard_dict)
	schedule.every().day.at(serve.Shifts.ShiftA.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.Shifts.ShiftB.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.Shifts.ShiftC.start_time.strftime("%H:%M:%S")).do(shift_end_activity,)
	schedule.every().day.at(serve.OEE.ShiftA.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftA)
	schedule.every().day.at(serve.OEE.ShiftB.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftB)
	schedule.every().day.at(serve.OEE.ShiftC.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, serve.Shifts.ShiftC)
	schedule.every().day.at(serve.OEE.ShiftC.generate_oee_time.strftime("%H:%M:%S")).do(generate_oee_data, )
	schedule.every().day.at(serve.OEE.ShiftA.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	schedule.every().day.at(serve.OEE.ShiftB.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(oee_down_time_auto_acceptence,)
	schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail,)
	schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,production_day_summary_report_mail,)
	# schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail,)
	# schedule.every().day.at(serve.OEE.day_ml_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,major_loss_events_of_day_mail,)
	# schedule.every().day.at(serve.OEE.day_pn_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,part_number_mail,)
	schedule.every().day.at(serve.OEE.day_plan_vs_actual_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,production_plan_vs_actual_mail,)
	schedule.every().day.at(serve.OEE.ShiftA.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftA,))
	schedule.every().day.at(serve.OEE.ShiftB.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftB,))
	schedule.every().day.at(serve.OEE.ShiftC.oee_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_report_mail, args = (serve.Shifts.ShiftC,))
	# schedule.every().day.at(serve.OEE.ShiftA.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftA,))
	# schedule.every().day.at(serve.OEE.ShiftB.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftB,))
	# schedule.every().day.at(serve.OEE.ShiftC.dt_report_mail_time.strftime("%H:%M:%S")).do(serve.run_as_thread,oee_down_time_distribuition_mail, args = (serve.Shifts.ShiftC,))
