import serial, struct, time, logging, datetime, queue, schedule, math
from dateutil.relativedelta import relativedelta
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.db.utils import ProgrammingError
from django.db.models import Q, F, Sum, When, Case, Value, Avg
from django.db.models.functions import Coalesce

from xylem.settings import EMAIL_HOST_USER, XYLEM_MODE, XYLEM_MODE_DIC
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a009_building_management_system.models import minutes_period, max_minute_period, twf_hp_list, WaterFlowData, WaterFlowCumData, WaterFlowLastReadData, twf_hp_list


a009_bw_logger = logging.getLogger(serve.Apps.A009BuildingManagementSystem.bw_logger_name)

serial_rs485_wait_time_for_reply_in_secs = 0.15

hour_name_list = []
for hour in range(24):
	hour_name_list.append("{:02d}:00 - {:02d}:00".format(hour,hour+1 if hour+1!=24 else 0))


# Below are power consumption dashboard dict details
# All power consumptions are in units (kwh)
pc_dashboard_dict = {
    "tt": "",
    "ddt": "",
    
    "dc_n": serve.a009_pc_dashboard_day_cum_name,
	"dc_c": "", 
	"dc_cr": "", 
	"dc_crc": "", 
	"dc_crct": 0, 
	"dc_ll": "",
    
	"mc_n": serve.a009_pc_dashboard_month_cum_name,
	"mc_c": "",
	"mc_cr": "",
	"mc_crc": "", 
	"mc_crct": 0, 

    "ic_eb_n": serve.a009_pc_dashboard_income_eb_cum_name,
	"ic_eb_ds": "", 
	"ic_eb_ms": "", 
	"ic_eb_if": "", 

	"ic_dg_n": serve.a009_pc_dashboard_income_dg_cum_name,
	"ic_dg_ds": "", 
	"ic_dg_ms": "", 
	"ic_dg_if": "", 
}


# Below are water consumption dashboard dict details
# All water consumptions are in liters,
# Exception month consumption rate, all consumption rates are in liters/hour, whereas month consumption is liters/day
# tt : time text, ddt : date day text
# dc_n: day cumulative name, dc_c: day cumulative consumption,
# dc_cr: day cumulative consumption rate, dc_crc: day cumulative consumption rate change,
# dc_crct: day cumulative consumption rate change type,
# dc_if: day cumulative instantaneous flow,
# s1_n: section 1 name, s1_bg_c: section 1 background color,  s1_c: section 1 consumption,
# s1_cr: section 1 consumption rate, s1_crc: section 1 consumption rate change,
# s1_crct: section 1 consumption rate change type,
# s1_if: section 1 instantaneous flow,
# s2_n: section 2 name, s2_bg_c: section 2 background color, s2_c: section 2 consumption,
# s2_cr: section 2 consumption rate, s2_crc: section 2 consumption rate change,
# s2_crct: section 2 consumption rate change type,
# s2_if: section 2 instantaneous flow,
# s3_n: section 3 name, s3_bg_c: section 3 background color, s3_c: section 3 consumption,
# s3_cr: section 3 consumption rate, s3_crc: section 3 consumption rate change,
# s3_crct: section 3 consumption rate change type,
# s3_if: section 3 instantaneous flow,
# hrly_x_n: hourly chart x name,
# hrly_y_s1: hourly chart y section 1,
# hrly_y_s2: hourly chart y section 2,
# hrly_y_s3: hourly chart y section 3,
# mc_n: monthly cumulative name, mc_c: monthly cumulative consumption,
# mc_cr: monthly cumulative consumption rate, mc_crc: monthly cumulative consumption rate change,
# mc_crct: monthly cumulative consumption rate change type,
# mc_c: monthly cumulative consumption,
# ic_n: incoming cumulative name, ic_ds: incoming cumulative day supply,
# ic_ms: incoming cumulative month supply, 
# ic_if: incoming cumulative instantaneous flow,

wc_dashboard_dict = {
    "tt": "",
    "ddt": "",
    
    "dc_n": serve.a009_wc_dashboard_day_cum_name,
	"dc_c": "", 
	"dc_cr": "", 
	"dc_crc": "", 
	"dc_crct": 0, 
	"dc_if": "",
    
    "s1_n": serve.a009_wc_dashboard_section1_name,
    "s1_bg_c": serve.a009_wc_dashboard_section1_bg_color,
	"s1_c": "", 
	"s1_cr": "", 
	"s1_crc": "", 
	"s1_crct": 0, 
	"s1_if": "", 
    
    "s2_n": serve.a009_wc_dashboard_section2_name,
    "s2_bg_c": serve.a009_wc_dashboard_section2_bg_color,
	"s2_c": "", 
	"s2_cr": "", 
	"s2_crc": "", 
	"s2_crct": 0, 
	"s2_if": "", 
    
    "s3_n": serve.a009_wc_dashboard_section3_name,
    "s3_bg_c": serve.a009_wc_dashboard_section3_bg_color,
	"s3_c": "", 
	"s3_cr": "", 
	"s3_crc": "", 
	"s3_crct": 0, 
	"s3_if": "", 
    
    "hrly_x_n": hour_name_list,
    "hrly_y_s1": [],
    "hrly_y_s2": [],
    "hrly_y_s3": [],
    
	"mc_n": serve.a009_wc_dashboard_month_cum_name,
	"mc_c": "",
	"mc_cr": "",
	"mc_crc": "", 
	"mc_crct": 0, 

    "ic_n": serve.a009_wc_dashboard_income_cum_name,
	"ic_ds": "", 
	"ic_ms": "", 
	"ic_if": "", 
}


def get_number_as_human_format(num): # number with one digit human readable such as K, M, B, T
	if num >= 1_000_000_000_000:
		formatted = num / 1_000_000_000_000
		suffix = 'T'
	elif num >= 1_000_000_000:
		formatted = num / 1_000_000_000
		suffix = 'B'
	elif num >= 1_000_000:
		formatted = num / 1_000_000
		suffix = 'M'
	elif num >= 1_000:
		formatted = num / 1_000
		suffix = 'K'
	else:
		formatted = num
		suffix = ''
	formatted = round(formatted * 10)/10
	
	# Format without decimals if the number is an integer
	formatted = serve.convert_float_with_int_possibility(formatted, 1)
	return f"{formatted}{suffix}"
	

def days_of_month_till_dt(dt):
	# Determine the first day of the current month
	first_day_of_month = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

	# Calculate the difference in time between now and the start of the month
	time_difference = dt - first_day_of_month

	# Convert the difference to seconds
	seconds_elapsed = time_difference.total_seconds()

	# Convert seconds to days (1 day = 86,400 seconds)
	days_elapsed = seconds_elapsed / (24*60*60)  # 86400 seconds in a day

	return days_elapsed


def days_in_month(dt):
	year = dt.year
	month = dt.month

	# Get the first day of the next month
	if month == 12:
		next_month = datetime.datetime(year + 1, 1, 1)
	else:
		next_month = datetime.datetime(year, month + 1, 1)

	# Get the last day of the current month
	last_day_of_month = next_month - datetime.timedelta(days=1)

	# Return the day of the last day of the month
	return last_day_of_month.day

      

instantaneous_flow_start_add = 1447
instantaneous_flow_size = 2
# instantaneous flow value is taken as float in unit 'm3/h'

total_flow_start_add = 1453
total_flow_size = 2
# total flow value is taken as float in unit 'm3'

battery_voltage_start_add = 1455
battery_voltage_size = 2
# battery voltage is taken as float in unit 'V'


instantaneous_flow_start_add_hex ='{0:04X}'.format(instantaneous_flow_start_add-1)
instantaneous_flow_size_hex = '{0:04X}'.format(instantaneous_flow_size)
total_flow_start_add_hex ='{0:04X}'.format(total_flow_start_add-1)
total_flow_size_hex = '{0:04X}'.format(total_flow_size)
battery_voltage_start_add_hex ='{0:04X}'.format(battery_voltage_start_add-1)
battery_voltage_size_hex = '{0:04X}'.format(battery_voltage_size)

flow_meter_dict = {}
total_flow_data_queue = queue.Queue(maxsize=30)

# rs485_device_id: rs485 device id, name: name of the flow meter,
# tf_hp_i: total flow hour period index, if: instantaneous flow, otf: old total flow, ntf: new total flow, bv: battery voltage
sub_flow_meter_dict_default = {"rs485_device_id": None , "name": None, "tf_hp_i":None, "if": None, "otf": None, "ntf": None, "bv": None}

tf_hp_index = None

serial_rs485 = None
initial_connection_call = None

def routine_work():
    global tf_hp_index, current_time_time, current_time_datetime
    while True:
        current_time_time = time.time()
        current_time_datetime = datetime.datetime.now()
        temp_current_dt = current_time_datetime
        tf_hp_index = int(temp_current_dt.hour*60/minutes_period) + int(temp_current_dt.minute/minutes_period)
        time.sleep(0.2)


def get_crc16(data: bytes) -> int:
    crc = 0xFFFF
    polynomial = 0xA001

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if (crc & 0x0001):
                crc = (crc >> 1) ^ polynomial
            else:
                crc >>= 1
    crc_value = crc & 0xFFFF
    swapped_crc_value = (crc_value >> 8) | ((crc_value & 0xFF) << 8)
    return swapped_crc_value


def validate_checksum(data: bytes) -> bool:
	recv_checksum = data[-2:]
	crc = get_crc16(data[:-2])
	actual_checksum = bytes.fromhex('{0:04X}'.format(crc))
	return recv_checksum == actual_checksum


def connect_serial():
	global serial_rs485, initial_connection_call
	while True:
		try:
			serial_rs485 = serial.Serial(serve.a009_wc_com_port,
				baudrate = 9600,
				parity = serial.PARITY_NONE,
				stopbits = serial.STOPBITS_ONE,
				bytesize = serial.EIGHTBITS,
				timeout = 1
			)
			print(f"Connection established successfully {serve.a009_wc_com_port}")
			break
		except Exception as e:
			a009_bw_logger.error("Exception occurred", exc_info=True)
			if initial_connection_call:
				break
			print(f"Unable to connect {serve.a009_wc_com_port},  Do plug the rs485 cable")
		time.sleep(1)


def get_pc_dashboard_dict():
    return pc_dashboard_dict


def wc_read_instantaneous_flow(rs485_device_id):
	if not serial_rs485:
		connect_serial()
	temp_data = bytes.fromhex('{0:02X}'.format(rs485_device_id)+'03'+instantaneous_flow_start_add_hex+instantaneous_flow_size_hex)
	crc = get_crc16(temp_data)
	send_data = temp_data + bytes.fromhex('{0:04X}'.format(crc))
	serial_rs485.write(send_data)
	time.sleep(serial_rs485_wait_time_for_reply_in_secs)
	recv_data=serial_rs485.read_all()
	assert validate_checksum(recv_data)
	temp_data = recv_data[3:][:4]
	return struct.unpack('>f', temp_data[2:]+temp_data[:2])[0]

	
def wc_read_total_flow(rs485_device_id):
	if not serial_rs485:
		connect_serial()
	temp_data = bytes.fromhex('{0:02X}'.format(rs485_device_id)+'03'+total_flow_start_add_hex+total_flow_size_hex)
	crc = get_crc16(temp_data)
	send_data = temp_data + bytes.fromhex('{0:04X}'.format(crc))
	serial_rs485.write(send_data)
	time.sleep(serial_rs485_wait_time_for_reply_in_secs)
	recv_data = serial_rs485.read_all()
	assert validate_checksum(recv_data)
	temp_data = recv_data[3:][:4]
	return struct.unpack('>f', temp_data[2:]+temp_data[:2])[0]


def wc_read_battery_voltage(rs485_device_id):
	if not serial_rs485:
		connect_serial()
	temp_data = bytes.fromhex('{0:02X}'.format(rs485_device_id)+'03'+battery_voltage_start_add_hex+battery_voltage_size_hex)
	crc = get_crc16(temp_data)
	send_data = temp_data + bytes.fromhex('{0:04X}'.format(crc))
	serial_rs485.write(send_data)
	time.sleep(serial_rs485_wait_time_for_reply_in_secs)
	recv_data = serial_rs485.read_all()#[len(send_data):]
	assert validate_checksum(recv_data)
	temp_data = recv_data[3:][:4]
	return struct.unpack('>f', temp_data[2:]+temp_data[:2])[0]


def wc_update_dict():
	global serial_rs485
	logged_flag = False
	ser_ex_logged_flag = False
	assert_ex_logged_flag = False
	while True:
		for fm_id in flow_meter_dict:
			continue_count = 0
			while True:
				try:
					flow_meter_dict[fm_id]["if"] = wc_read_instantaneous_flow(flow_meter_dict[fm_id]["rs485_device_id"]) * 1000
					temp_ntf = wc_read_total_flow(flow_meter_dict[fm_id]["rs485_device_id"]) * 1000
					if flow_meter_dict[fm_id]["ntf"] and flow_meter_dict[fm_id]["otf"]:
						a009_bw_logger.info(f"ASDF fm_id: {fm_id}, otf: {flow_meter_dict[fm_id]['otf']}, ntf: {flow_meter_dict[fm_id]['ntf']}, temp_ntf: {temp_ntf}, diff(ntf,otf) :{flow_meter_dict[fm_id]['ntf'] - flow_meter_dict[fm_id]['otf']}, diff(temp_ntf,ntf) :{temp_ntf - flow_meter_dict[fm_id]['ntf']} ")
					if flow_meter_dict[fm_id]["ntf"] and (temp_ntf - flow_meter_dict[fm_id]["ntf"] > 500):
						a009_bw_logger.warning(f"Total flow jump observed, flow meter icode: {fm_id}, old ntf: {flow_meter_dict[fm_id]['ntf']}, new ntf: {temp_ntf}")
						flow_meter_dict[fm_id]["otf"] = flow_meter_dict[fm_id]["otf"] + temp_ntf - flow_meter_dict[fm_id]["ntf"]
					flow_meter_dict[fm_id]["ntf"] = temp_ntf
					if logged_flag:
						logged_flag = False
					if ser_ex_logged_flag:
						ser_ex_logged_flag = False
					if assert_ex_logged_flag:
						assert_ex_logged_flag = False
				except AssertionError:
					if not assert_ex_logged_flag:
						a009_bw_logger.warning(f"Assertion serial occurred, flow meter icode: {fm_id} ", exc_info=True)
						assert_ex_logged_flag = True
					if continue_count <= 1: # limiting to 3 times
						continue_count = continue_count + 1
						continue
				except serial.SerialException:
					if not ser_ex_logged_flag:
						a009_bw_logger.error(f"Exception serial occurred, flow meter icode: {fm_id} ", exc_info=True)
						ser_ex_logged_flag = True
					serial_rs485 = None
				except Exception as e:
					if not logged_flag:
						a009_bw_logger.error(f"Exception occurred, flow meter icode: {fm_id} ", exc_info=True)
						logged_flag = True
				break
		time.sleep(0.5)


def wc_total_flow_data_generator(fm_id):
    logged_flag = False
    while True:
        try:
            if tf_hp_index != flow_meter_dict[fm_id]["tf_hp_i"]:
                if flow_meter_dict[fm_id]["ntf"]!=None:
                    twf = flow_meter_dict[fm_id]["ntf"]-flow_meter_dict[fm_id]["otf"]
                    if twf < 0:
                        a009_bw_logger.warning(f'water flow negative value observed, {fm_id} ==> ntf:{flow_meter_dict[fm_id]["ntf"]}, otf:{flow_meter_dict[fm_id]["otf"]}, tf:{flow_meter_dict[fm_id]["ntf"]-flow_meter_dict[fm_id]["otf"]}')
                        twf = 0
                    total_flow_data_queue.put([flow_meter_dict[fm_id]["ntf"], twf, fm_id, flow_meter_dict[fm_id]["tf_hp_i"], current_time_datetime-datetime.timedelta(seconds=10)])
                    flow_meter_dict[fm_id]["otf"] =  flow_meter_dict[fm_id]["ntf"]
                flow_meter_dict[fm_id]["tf_hp_i"] = tf_hp_index
            time.sleep(1)
            if logged_flag:
                logged_flag=False
        except Exception as e:
            if not logged_flag:
                a009_bw_logger.error("Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(serve.error_wait)


def wc_send_basic_report(current_date):
	subject = f"X-A009: Water Consumption Report ({serve.PlantLocations.SP_Koil.name}) - {current_date}"
	text_content = ""
	to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a009_water_consumption_report_p1_mail)
	month_data = WaterFlowCumData.objects.filter(date__month = current_date.month, date__year = current_date.year, date__lte = current_date) 
	s1_d_c = month_data.filter(date = current_date, flow_meter_i__in = serve.Others.a009_s1_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
	s2_d_c = month_data.filter(date = current_date, flow_meter_i__in = serve.Others.a009_s2_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
	s3_d_c = month_data.filter(date = current_date, flow_meter_i__in = serve.Others.a009_s3_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
	inlet_d_s = month_data.filter(date = current_date, flow_meter_i__in = serve.Others.a009_income_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
	s1_m_c = month_data.filter(flow_meter_i__in = serve.Others.a009_s1_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
	s2_m_c = month_data.filter(flow_meter_i__in = serve.Others.a009_s2_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
	s3_m_c = month_data.filter(flow_meter_i__in = serve.Others.a009_s3_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
	inlet_m_s = month_data.filter(flow_meter_i__in = serve.Others.a009_income_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
	context = {
		"current_date": current_date,
		"section_data": [
			{"name": wc_dashboard_dict['s1_n'], "bg_c": wc_dashboard_dict['s1_bg_c'], "day_c": serve.convert_float_with_int_possibility(s1_d_c, 1), "month_c": serve.convert_float_with_int_possibility(s1_m_c, 1)},
			{"name": wc_dashboard_dict['s2_n'], "bg_c": wc_dashboard_dict['s2_bg_c'], "day_c": serve.convert_float_with_int_possibility(s2_d_c, 1), "month_c": serve.convert_float_with_int_possibility(s2_m_c, 1)},
			{"name": wc_dashboard_dict['s3_n'], "bg_c": wc_dashboard_dict['s3_bg_c'], "day_c": serve.convert_float_with_int_possibility(s3_d_c, 1), "month_c": serve.convert_float_with_int_possibility(s3_m_c, 1)},
		],
		"tot_data":{
			"day": serve.convert_float_with_int_possibility(s1_d_c + s2_d_c + s3_d_c, 1),
			"month": serve.convert_float_with_int_possibility(s1_m_c + s2_m_c + s3_m_c, 1),
		},
		"inlet_data":{
			"day": serve.convert_float_with_int_possibility(inlet_d_s, 1),
			"month": serve.convert_float_with_int_possibility(inlet_m_s, 1),
		}
	}
	html_content = render_to_string('a009/wc_report_mail.html', context)
	serve.send_mail(app_name = serve.an_building_management_system, subject = subject, to_list = to_list, html_content = html_content)
	

def wc_generate_day_cum_data():
	pre_date = (current_time_datetime - datetime.timedelta(days=1)).date()
	for fm_id in flow_meter_dict:
		twf_col_list = WaterFlowData.objects.filter(flow_meter_i_id=fm_id, date=pre_date).values_list(*twf_hp_list).first() or []
		WaterFlowCumData.objects.create(
			flow_meter_i_id = fm_id,
			date = pre_date,
			twf = sum(filter(None, twf_col_list)),
		)
	wc_send_basic_report(pre_date)


def wc_move_total_flow_data():
	logged_flag = False
	while True:
		try:
			tf, twf, fm_id, tf_hp_index, dt = total_flow_data_queue.get()
			tfd = WaterFlowData.objects.filter(flow_meter_i_id = fm_id, date = dt.date())
			last_data_object = WaterFlowLastReadData.objects.get(flow_meter_i_id = fm_id)
			last_data_object.tf = tf
			last_data_object.save()
			if tfd.exists():
				tfdf = tfd.first()
				setattr(tfdf, twf_hp_list[tf_hp_index], twf)
				tfdf.save()
			else:	
				temp_dict = {"flow_meter_i_id": fm_id , f"{twf_hp_list[tf_hp_index]}": twf, "date": dt.date()}
				WaterFlowData.objects.create(**temp_dict)
			if logged_flag:
				logged_flag=False
		except Exception as e:
			if not logged_flag:
				a009_bw_logger.error(f"Exception occurred {twf}, {fm_id}, {tf_hp_index}, {dt}", exc_info=True)
				logged_flag=True
			time.sleep(serve.error_wait)


def update_wc_dashboard_dict():
	last_updated_date = None
	logged_flag = False
	while True:
		try:
			current_dt = current_time_datetime
			current_d = current_dt.date()
			previous_d_dt = current_dt - datetime.timedelta(days=1)
			previous_m_dt = current_dt - relativedelta(month=1)

			wc_dashboard_dict["tt"] =   current_dt.strftime("%I:%M:%S %p")
			wc_dashboard_dict["ddt"] =  " ".join([current_dt.strftime("%d-%b-%Y"), current_dt.strftime("%a")])
			if last_updated_date != current_d:
				cur_hr_no = 1
				day_start_dt = serve.get_start_of_the_day(current_dt)
				period_start = day_start_dt
				period_end = day_start_dt
				wc_dashboard_dict["hrly_y_s1"] = []
				wc_dashboard_dict["hrly_y_s2"] = []
				wc_dashboard_dict["hrly_y_s3"] = []
				income_fm_data_list = []
				last_updated_date = current_d

			hourly_list = []
			while period_end != current_dt:
				period_end =  day_start_dt + datetime.timedelta(hours=cur_hr_no)
				if period_end>=current_dt:
					period_end = current_dt
					temp_period_start = period_start
					temp_list = []
					while temp_period_start<period_end-datetime.timedelta(minutes=minutes_period):
						temp_list.append(f'tf_H{temp_period_start.hour}P{int(temp_period_start.minute/minutes_period)}')
						temp_period_start = temp_period_start + datetime.timedelta(minutes=minutes_period)
					hourly_list.append(temp_list)
				else:
					temp_list = []
					while period_start<period_end:
						temp_list.append(f'tf_H{period_start.hour}P{int(period_start.minute/minutes_period)}')
						period_start = period_start + datetime.timedelta(minutes=minutes_period)
					hourly_list.append(temp_list)
					cur_hr_no = cur_hr_no+1

			total_hours = (current_dt - day_start_dt).total_seconds()/(60*60)

			s1_tf_ch = 0
			s1_if = 0
			for fm in serve.Others.a009_s1_cosumption_flow_meters_list:
				fm_id = fm.icode
				if flow_meter_dict[fm_id]["ntf"]!=None:
					s1_tf_ch = s1_tf_ch + flow_meter_dict[fm_id]["ntf"] - flow_meter_dict[fm_id]["otf"]
				if flow_meter_dict[fm_id]["if"]!=None:
					s1_if = s1_if + flow_meter_dict[fm_id]["if"]

			s2_tf_ch = 0
			s2_if = 0
			for fm in serve.Others.a009_s2_cosumption_flow_meters_list:
				fm_id = fm.icode
				if flow_meter_dict[fm_id]["ntf"]!=None:
					s2_tf_ch = s2_tf_ch + flow_meter_dict[fm_id]["ntf"] - flow_meter_dict[fm_id]["otf"]
				if flow_meter_dict[fm_id]["if"]!=None:
					s2_if = s2_if + flow_meter_dict[fm_id]["if"]
			
			s3_tf_ch = 0
			s3_if = 0
			for fm in serve.Others.a009_s3_cosumption_flow_meters_list:
				fm_id = fm.icode
				if flow_meter_dict[fm_id]["ntf"]!=None:
					s3_tf_ch = s3_tf_ch + flow_meter_dict[fm_id]["ntf"] - flow_meter_dict[fm_id]["otf"]
				if flow_meter_dict[fm_id]["if"]!=None:
					s3_if = s3_if + flow_meter_dict[fm_id]["if"]

			ic_tf_ch = 0
			ic_if = 0
			for fm in serve.Others.a009_income_flow_meters_list:
				fm_id = fm.icode
				if flow_meter_dict[fm_id]["ntf"]!=None:
					ic_tf_ch = ic_tf_ch + flow_meter_dict[fm_id]["ntf"] - flow_meter_dict[fm_id]["otf"]
				if flow_meter_dict[fm_id]["if"]!=None:
					ic_if = ic_if + flow_meter_dict[fm_id]["if"]

			for index_i, hrly_periods_list in enumerate(hourly_list):
				index_ele = cur_hr_no-1
				if index_i==len(hourly_list)-1:
					s1_tf, s2_tf, s3_tf, ic_tf = s1_tf_ch, s2_tf_ch, s3_tf_ch, ic_tf_ch
				else:
					s1_tf, s2_tf, s3_tf, ic_tf = 0, 0, 0, 0

				if hrly_periods_list:
					temp_col_data = WaterFlowData.objects.filter(date=current_d, flow_meter_i__in=serve.Others.a009_s1_cosumption_flow_meters_list).values_list(*hrly_periods_list)
					for li in temp_col_data:
						s1_tf = s1_tf + sum(filter(None, li))
				if len(wc_dashboard_dict["hrly_y_s1"])!=cur_hr_no:
					wc_dashboard_dict["hrly_y_s1"].append(s1_tf)
				else:
					wc_dashboard_dict["hrly_y_s1"][index_ele] = s1_tf
				
				if hrly_periods_list:
					temp_col_data = WaterFlowData.objects.filter(date=current_d, flow_meter_i__in=serve.Others.a009_s2_cosumption_flow_meters_list).values_list(*hrly_periods_list)
					for li in temp_col_data:
						s2_tf = s2_tf + sum(filter(None, li))
				if len(wc_dashboard_dict["hrly_y_s2"])!=cur_hr_no:
					wc_dashboard_dict["hrly_y_s2"].append(s2_tf)
				else:
					wc_dashboard_dict["hrly_y_s2"][index_ele] = s2_tf

				if hrly_periods_list:
					temp_col_data = WaterFlowData.objects.filter(date=current_d, flow_meter_i__in=serve.Others.a009_s3_cosumption_flow_meters_list).values_list(*hrly_periods_list)
					for li in temp_col_data:
						s3_tf = s3_tf + sum(filter(None, li))
				if len(wc_dashboard_dict["hrly_y_s3"])!=cur_hr_no:
					wc_dashboard_dict["hrly_y_s3"].append(s3_tf)
				else:
					wc_dashboard_dict["hrly_y_s3"][index_ele] = s3_tf

				if hrly_periods_list:
					temp_col_data = WaterFlowData.objects.filter(date=current_d, flow_meter_i__in=serve.Others.a009_income_flow_meters_list).values_list(*hrly_periods_list)
					for li in temp_col_data:
						ic_tf = ic_tf + sum(filter(None, li))
				if len(income_fm_data_list)!=cur_hr_no:
					income_fm_data_list.append(ic_tf)
				else:
					income_fm_data_list[index_ele] = ic_tf
			
			s1_c = sum(wc_dashboard_dict["hrly_y_s1"])
			s1_cr = s1_c/total_hours
			s1_cr_previous_d = WaterFlowCumData.objects.filter(date = previous_d_dt, flow_meter_i__in = serve.Others.a009_s1_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0)/24)["cum_twf"]
			if s1_cr_previous_d is NotImplemented:
				s1_cr_previous_d = 0.0
			s1_crc = serve.convert_float_with_int_possibility(((s1_cr - s1_cr_previous_d)/(s1_cr_previous_d or 1))*100,1)
			wc_dashboard_dict["s1_c"] = get_number_as_human_format(s1_c)
			wc_dashboard_dict["s1_cr"] = get_number_as_human_format(s1_cr)
			wc_dashboard_dict["s1_crc"] = f"{abs(s1_crc)}%"
			if s1_crc < 0:
				wc_dashboard_dict["s1_crct"] = -1
			elif s1_crc > 0:
				wc_dashboard_dict["s1_crct"] = 1
			else:
				wc_dashboard_dict["s1_crct"] = 0
			wc_dashboard_dict["s1_if"] = get_number_as_human_format(s1_if)

			s2_c = sum(wc_dashboard_dict["hrly_y_s2"])
			s2_cr = s2_c/total_hours
			s2_cr_previous_d = WaterFlowCumData.objects.filter(date = previous_d_dt, flow_meter_i__in = serve.Others.a009_s2_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0)/24)["cum_twf"]
			if s2_cr_previous_d is NotImplemented:
				s2_cr_previous_d = 0.0
			s2_crc = serve.convert_float_with_int_possibility(((s2_cr - s2_cr_previous_d)/(s2_cr_previous_d or 1))*100,1)
			wc_dashboard_dict["s2_c"] = get_number_as_human_format(s2_c)
			wc_dashboard_dict["s2_cr"] = get_number_as_human_format(s2_cr)
			wc_dashboard_dict["s2_crc"] = f"{abs(s2_crc)}%"
			if s2_crc < 0:
				wc_dashboard_dict["s2_crct"] = -1
			elif s2_crc > 0:
				wc_dashboard_dict["s2_crct"] = 1
			else:
				wc_dashboard_dict["s2_crct"] = 0
			wc_dashboard_dict["s2_if"] = get_number_as_human_format(s2_if)

			s3_c = sum(wc_dashboard_dict["hrly_y_s3"])
			s3_cr = s3_c/total_hours
			s3_cr_previous_d = WaterFlowCumData.objects.filter(date = previous_d_dt, flow_meter_i__in = serve.Others.a009_s3_cosumption_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0)/24)["cum_twf"]
			if s3_cr_previous_d is NotImplemented:
				s3_cr_previous_d = 0.0
			s3_crc = serve.convert_float_with_int_possibility(((s3_cr - s3_cr_previous_d)/(s3_cr_previous_d or 1))*100,1)
			wc_dashboard_dict["s3_c"] = get_number_as_human_format(s3_c)
			wc_dashboard_dict["s3_cr"] = get_number_as_human_format(s3_cr)
			wc_dashboard_dict["s3_crc"] = f"{abs(s3_crc)}%"
			if s3_crc < 0:
				wc_dashboard_dict["s3_crct"] = -1
			elif s3_crc > 0:
				wc_dashboard_dict["s3_crct"] = 1
			else:
				wc_dashboard_dict["s3_crct"] = 0
			wc_dashboard_dict["s3_if"] = get_number_as_human_format(s3_if)

			dc_c = s1_c + s2_c + s3_c
			dc_cr = s1_cr + s2_cr + s3_cr
			dc_cr_previous_d = s1_cr_previous_d + s2_cr_previous_d + s3_cr_previous_d
			dc_crc = serve.convert_float_with_int_possibility(((dc_cr - dc_cr_previous_d)/(dc_cr_previous_d or 1))*100,1)
			wc_dashboard_dict["dc_c"] = get_number_as_human_format(dc_c)
			wc_dashboard_dict["dc_cr"] = get_number_as_human_format(dc_cr)
			wc_dashboard_dict["dc_crc"] = f"{abs(dc_crc)}%"
			if dc_crc < 0:
				wc_dashboard_dict["dc_crct"] = -1
			elif dc_crc > 0:
				wc_dashboard_dict["dc_crct"] = 1
			else:
				wc_dashboard_dict["dc_crct"] = 0
			wc_dashboard_dict["dc_if"] = get_number_as_human_format(s1_if+s2_if+s3_if)

			mc_c = dc_c + WaterFlowCumData.objects.filter(date__month = current_d.month, date__year = current_d.year,  date__lt = current_d).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
			mc_cr = mc_c / days_of_month_till_dt(current_dt)
			mc_cr_previous_m = WaterFlowCumData.objects.filter(date__month = previous_m_dt.month, date__year = current_d.year,).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0)/days_in_month(previous_m_dt))["cum_twf"]
			mc_crc = serve.convert_float_with_int_possibility(((mc_cr - mc_cr_previous_m)/(mc_cr_previous_m or 1))*100,1)
			wc_dashboard_dict["mc_c"] = get_number_as_human_format(mc_c)
			wc_dashboard_dict["mc_cr"] = get_number_as_human_format(mc_cr)
			wc_dashboard_dict["mc_crc"] = f"{abs(mc_crc)}%"
			if mc_crc < 0:
				wc_dashboard_dict["mc_crct"] = -1
			elif mc_crc > 0:
				wc_dashboard_dict["mc_crct"] = 1
			else:
				wc_dashboard_dict["mc_crct"] = 0

			ic_ds = sum(income_fm_data_list)
			ic_ms = ic_ds + WaterFlowCumData.objects.filter(date__month = current_d.month, date__lt = current_d, flow_meter_i__in=serve.Others.a009_income_flow_meters_list).aggregate(cum_twf = Coalesce(Sum("twf"), 0.0))["cum_twf"]
			wc_dashboard_dict["ic_ds"] = get_number_as_human_format(ic_ds)
			wc_dashboard_dict["ic_ms"] = get_number_as_human_format(ic_ms)
			wc_dashboard_dict["ic_if"] = get_number_as_human_format(ic_if)
			if logged_flag:
				logged_flag = False
			time.sleep(1)
		except Exception as e:
			if not logged_flag:
				a009_bw_logger.error("Exception occurred", exc_info=True)
				logged_flag=True
			time.sleep(serve.error_wait)
	

def get_wc_dashboard_dict():
    return wc_dashboard_dict


serve.run_as_thread(routine_work)

try:
	same_day_twf_hp_list=[]
	current_dt = current_time_datetime
	end_hour = current_dt.hour
	end_hour_minute = current_dt.minute
	for hour in range(0, end_hour):
		for j in range(max_minute_period):
			same_day_twf_hp_list.append(f'tf_H{hour}P{j}')
	for p in range(int(end_hour_minute/minutes_period)):
		same_day_twf_hp_list.append(f'tf_H{end_hour}P{p}')
    
	fms = serve.get_flow_meters()
	for fm in fms:
		fm_id = fm.icode	
		flow_meter_dict[fm_id] = sub_flow_meter_dict_default.copy()
		flow_meter_dict[fm_id]["name"] = fm.name
		flow_meter_dict[fm_id]["rs485_device_id"] = int(fm.description)
		try:
			initial_connection_call = True
			# if XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
			tf = wc_read_total_flow(flow_meter_dict[fm_id]["rs485_device_id"]) * 1000
			# else:
			# 	tf = 0
		except: 
			tf = 0
		last_data_object, created = WaterFlowLastReadData.objects.get_or_create(flow_meter_i_id = fm_id, defaults = {'tf': tf})
		if not created:
			if tf and last_data_object.tf > tf:
				temp_tf = last_data_object.tf
				last_data_object.tf = tf
				last_data_object.save()
				a009_bw_logger.warning(f"Flow meter {fm_id} last read data object updated with new value: {last_data_object.tf}, old value: {temp_tf}")
		flow_meter_dict[fm_id]["otf"] = last_data_object.tf
		serve.run_as_thread(wc_total_flow_data_generator, args = (fm_id,))
except (ProgrammingError, WaterFlowData.DoesNotExist) as e:
    a009_bw_logger.error("Exception occurred", exc_info=True)
except (ProgrammingError, WaterFlowCumData.DoesNotExist) as e:
    a009_bw_logger.error("Exception occurred", exc_info=True)
except (ProgrammingError, WaterFlowLastReadData.DoesNotExist) as e:
    a009_bw_logger.error("Exception occurred", exc_info=True)
initial_connection_call = False


if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
	# serve.run_as_thread(wc_update_dict)
	# serve.run_as_thread(wc_move_total_flow_data)
	# serve.run_as_thread(update_wc_dashboard_dict)
	# schedule.every().day.at("00:00:00").do(serve.run_as_thread,wc_generate_day_cum_data,)
	pass

elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
	# serve.run_as_thread(wc_update_dict)
	# serve.run_as_thread(wc_move_total_flow_data)
	# serve.run_as_thread(update_wc_dashboard_dict)
	# schedule.every().day.at("00:00:00").do(serve.run_as_thread,wc_generate_day_cum_data,)
	pass

elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
	serve.run_as_thread(wc_update_dict)
	serve.run_as_thread(wc_move_total_flow_data)
	serve.run_as_thread(update_wc_dashboard_dict)
	schedule.every().day.at("00:00:00").do(serve.run_as_thread,wc_generate_day_cum_data,)