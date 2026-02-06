import os, sys, time, threading, queue, socket, psutil, snap7, fins.udp, configparser, logging
from aphyt import omron
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s  - %(funcName)s - (Line no : %(lineno)d) %(message)s')
def get_rotating_file_logger(log_name, level):
    handler = RotatingFileHandler(log_name, mode='a', maxBytes=5*1024*1024, 
                                    backupCount=2, encoding=None, delay=1)
    handler.setFormatter(log_formatter)
    handler.addFilter(lambda record: record.levelno == level)
    handler.setLevel(level)
    return handler

app_log = logging.getLogger('root')
app_log.addHandler(get_rotating_file_logger("logs/xylem_cilent_error.log", logging.ERROR))
app_log.addHandler(get_rotating_file_logger("logs/xylem_cilent_info.log", logging.INFO))
app_log.setLevel(logging.INFO)

name_list=os.path.basename(__file__).split('.')
name_list[-1]="exe" 
exe_name_list=["_x64_hidden.".join(name_list), "_x64_visible.".join(name_list), "_x86_hidden.".join(name_list), "_x86_visible.".join(name_list)]
process_count=0
for p in psutil.process_iter():
    if p.name() in exe_name_list:
        process_count=process_count+1
    if process_count>1:
        app_log.info(f"Already execution file ran {exe_name_list} process count: {process_count}, Software exited")
        sys.exit()       

app_log.info(f'I am A007 OEE Monitring cilent, Software started')
config_file = configparser.ConfigParser()
config_file.read('client_settings.ini')

current_pc_stn_config = config_file.get('CURRENT_PC_STN_CONFIG','CURRENT_PC_STN_NAME')
ipaddress_or_name_of_server_system = config_file.get('CURRENT_PC_STN_CONFIG','ipaddress_or_name_of_server_system')
port_of_server_system = int(config_file.get('CURRENT_PC_STN_CONFIG','port_of_server_system'))
max_size_server_queue = int(config_file.get('CURRENT_PC_STN_CONFIG','maximum_size_server_queue'))
error_wait = int(config_file.get('CURRENT_PC_STN_CONFIG','error_wait_in_milliseconds'))/1000
server_thread_monitor_and_reconnect_delay = int(config_file.get('CURRENT_PC_STN_CONFIG','server_thread_monitor_and_reconnect_delay_in_milliseconds'))/1000

ps_list = []
ipaddresses_of_siemens_plc = config_file.get(current_pc_stn_config,'ipaddresses_of_siemens_plc_seperated_by_comma_respectively').split(',')
if ipaddresses_of_siemens_plc[0]:
    db_numbers_of_siemens_plc_respectively = config_file.get(current_pc_stn_config,'data_block_numbers_of_siemens_plc_seperated_by_comma_respectively').split(',')
    rack_numbers_of_siemens_plc_respectively = config_file.get(current_pc_stn_config,'rack_numbers_of_siemens_plc_seperated_by_comma_respectively').split(',')
    slot_numbers_of_siemens_plc_respectively = config_file.get(current_pc_stn_config,'slot_numbers_of_siemens_plc_seperated_by_comma_respectively').split(',')
    where_id_ps_for_siemens_plc = config_file.get(current_pc_stn_config,'where_id_of_production_station_for_siemens_plc_seperated_by_comma_respectively').split(',')
    is_this_a_production_station_of_siemens_plc_for_a007_oee_monitoring = config_file.get(current_pc_stn_config,'is_this_a_production_station_of_siemens_plc_for_a007_oee_monitoring_seperated_by_comma_respectively').split(',')
    is_this_a_production_station_of_siemens_plc_for_a009_process_ftr = config_file.get(current_pc_stn_config,'is_this_a_production_station_of_siemens_plc_for_a009_process_ftr_seperated_by_comma_respectively').split(',')
    siemens_plc_db_read_delay = int(config_file.get(current_pc_stn_config,'siemens_plc_db_read_delay_in_milliseconds'))/1000
    ps_list = ps_list + [int(ps) for ps in where_id_ps_for_siemens_plc]

ipaddresses_of_omron_CS_or_CJ_or_CP_plc = config_file.get(current_pc_stn_config,'ipaddresses_of_omron_CS_or_CJ_or_CP_plc_seperated_by_comma_respectively').split(',')
if ipaddresses_of_omron_CS_or_CJ_or_CP_plc[0]:
    destination_nodes_of_omron_CS_or_CJ_or_CP_plc = config_file.get(current_pc_stn_config,'destination_nodes_of_omron_CS_or_CJ_or_CP_plc_seperated_by_comma_respectively').split(',')
    source_nodes_of_omron_CS_or_CJ_or_CP_plc = config_file.get(current_pc_stn_config,'source_nodes_of_omron_CS_or_CJ_or_CP_plc_seperated_by_comma_respectively').split(',')
    start_word_addresses_of_omron_CS_or_CJ_or_CP_plc = config_file.get(current_pc_stn_config,'start_word_addresses_of_omron_CS_or_CJ_or_CP_plc_seperated_by_comma_respectively').split(',')
    where_id_ps_for_omron_CS_or_CJ_or_CP_plc = config_file.get(current_pc_stn_config,'where_id_of_production_station_for_omron_CS_or_CJ_or_CP_plc_seperated_by_comma_respectively').split(',')
    is_this_a_production_station_of_omron_CS_or_CJ_or_CP_plc_for_a007_oee_monitoring = config_file.get(current_pc_stn_config,'is_this_a_production_station_of_omron_CS_or_CJ_or_CP_plc_for_a007_oee_monitoring_seperated_by_comma_respectively').split(',')
    is_this_a_production_station_of_omron_CS_or_CJ_or_CP_plc_for_a009_process_ftr = config_file.get(current_pc_stn_config,'is_this_a_production_station_of_omron_CS_or_CJ_or_CP_plc_for_a009_process_ftr_seperated_by_comma_respectively').split(',')
    omron_CS_or_CJ_or_CP_plc_data_read_delay = int(config_file.get(current_pc_stn_config,'omron_CS_or_CJ_or_CP_plc_data_read_delay_in_milliseconds'))/1000
    ps_list = ps_list + [int(ps) for ps in where_id_ps_for_omron_CS_or_CJ_or_CP_plc]

ipaddresses_of_omron_NX_Series_plc = config_file.get(current_pc_stn_config,'ipaddresses_of_omron_NX_Series_plc_seperated_by_comma_respectively').split(',')
if ipaddresses_of_omron_NX_Series_plc[0]:
    omron_NX_Series_plc_data_read_delay = int(config_file.get(current_pc_stn_config,'omron_NX_Series_plc_data_read_delay_in_milliseconds'))/1000

server_queue = queue.Queue(maxsize=max_size_server_queue)
error_register_queue = queue.Queue()
data_queue = queue.Queue()

soc_parameters_from_server_flag = None

soc_a000_data_pack_size_byte_len = None
soc_a000_where_id_byte_len = None
soc_a000_what_id_byte_len = None
soc_a000_unique_no_byte_len = None

soc_a000_prod_data_sign = None
soc_a000_prod_data_sign_byte = None

soc_a000_production_interrupt_sign = None
soc_a000_production_interrupt_sign_up = None
soc_a000_production_interrupt_sign_down = None
soc_a000_production_interrupt_sign_byte = None

soc_a000_dept_passwords_sign = None
soc_a000_dept_passwords_sign_qa = None
soc_a000_dept_passwords_sign_mfg = None
soc_a000_dept_passwords_sign_ple = None
soc_a000_dept_passwords_sign_me = None
soc_a000_dept_passwords_sign_byte = None

soc_a007_oee_eve_cap_sign = None
soc_a007_oee_eve_cap_sign_popup = None
soc_a007_oee_eve_cap_sign_popdown = None
soc_a007_oee_eve_cap_sign_byte = None

soc_a007_manu_com_sign = None
soc_a007_manu_com_sign_byte = None

soc_a007_test_oee_eve_id_chat_sign = None
soc_a007_test_oee_eve_id_chat_sign_byte = None

soc_a009_process_data_sign = None
soc_a009_process_data_sign_ok = None
soc_a009_process_data_sign_nok = None
soc_a009_process_data_sign_byte = None


# prod_interrupt_msg_bytes:  production interrupt message in bytes
# prod_interrupt_msg_default_bytes:  production interrupt message default in bytes
# qa_pwd_bytes: quality password bytes, mfg_pwd_bytes: manufacturing password bytes,  ple_pwd_bytes: plant engineering password bytes,
# me_pwd_bytes: manufacturing engineering password bytes,

sub_dict_default = {
    "prod_interrupt_msg_bytes": None, "prod_interrupt_msg_default_bytes": None, "qa_pwd_bytes": None, "mfg_pwd_bytes": None,  "ple_pwd_bytes": None,  "me_pwd_bytes": None,
}

xylem_client_dic = {}
a000_unique_no = None
a007_oee_hmi_popup_list = []
a007_oee_hmi_popdown_list = []
a007_manu_com_msg_with_status_dic = {}

for index_i, i in enumerate(ipaddresses_of_siemens_plc):
  ipaddresses_of_siemens_plc[index_i] = i.strip()
for index_i, i in enumerate(ipaddresses_of_omron_CS_or_CJ_or_CP_plc):
  ipaddresses_of_omron_CS_or_CJ_or_CP_plc[index_i] = i.strip()
for index_i, i in enumerate(ipaddresses_of_omron_NX_Series_plc):
  ipaddresses_of_omron_NX_Series_plc[index_i] = i.strip()

zero = 0
one = 1
two = 2
three = 3
four = 4

siemens_db_software_beat_add = 0
siemens_db_part_no_add = 2	
siemens_db_unique_no_add = 34	
siemens_db_production_count_add = 36	
siemens_db_production_interrupt_add = 38	
siemens_db_production_interrupt_msg_add = 40	
siemens_db_oee_interrupt_add = 296	
siemens_db_oee_data_ready_add = 298	
siemens_db_oee_where_id_add = 300	
siemens_db_oee_what_id_add = 304	
siemens_db_qa_password_add = 308	
siemens_db_mfg_password_add = 320	
siemens_db_ple_password_add = 332	
siemens_db_me_password_add = 344	
siemens_db_manu_com_avl_add = 356	
siemens_db_manu_com_where_id_add = 358	
siemens_db_manu_com_what_id_add = 362
siemens_db_ftr_data_avl_add = 388
siemens_db_barcode_1_add = 390
siemens_db_barcode_2_add = 492
siemens_db_cycle_status_add = 594


siemens_db_total_bytes_to_read = 596
siemens_int_size = 2
siemens_long_int_size = 4

siemens_int_zero_in_bytes = zero.to_bytes(siemens_int_size, 'big')
siemens_int_one_in_bytes = one.to_bytes(siemens_int_size, 'big')
siemens_int_two_in_bytes = two.to_bytes(siemens_int_size, 'big')
siemens_int_three_in_bytes = three.to_bytes(siemens_int_size, 'big')
siemens_int_four_in_bytes = four.to_bytes(siemens_int_size, 'big')

siemens_long_int_zero_in_bytes = zero.to_bytes(siemens_long_int_size, 'big')

omron_cs_or_cj_or_cp_software_beat_byte_add = 0
omron_cs_or_cj_or_cp_part_no_byte_add = 2
omron_cs_or_cj_or_cp_unique_no_byte_add = 32
omron_cs_or_cj_or_cp_production_count_byte_add = 34
omron_cs_or_cj_or_cp_production_interrupt_byte_add = 36
omron_cs_or_cj_or_cp_production_interrupt_msg_byte_add = 38
omron_cs_or_cj_or_cp_oee_interrupt_byte_add = 294
omron_cs_or_cj_or_cp_oee_data_ready_byte_add = 296
omron_cs_or_cj_or_cp_oee_where_id_byte_add = 298
omron_cs_or_cj_or_cp_oee_what_id_byte_add = 302
omron_cs_or_cj_or_cp_qa_password_byte_add = 306
omron_cs_or_cj_or_cp_mfg_password_byte_add = 316
omron_cs_or_cj_or_cp_ple_password_byte_add = 326
omron_cs_or_cj_or_cp_me_password_byte_add = 336
omron_cs_or_cj_or_cp_manu_com_avl_byte_add = 346
omron_cs_or_cj_or_cp_manu_com_where_id_byte_add = 348
omron_cs_or_cj_or_cp_manu_com_what_id_byte_add = 352
omron_cs_or_cj_or_cp_ftr_data_avl_byte_add = 370
omron_cs_or_cj_or_cp_barcode_1_byte_add = 372
omron_cs_or_cj_or_cp_barcode_2_byte_add = 472
omron_cs_or_cj_or_cp_cycle_status_byte_add = 572

omron_cs_or_cj_or_cp_total_words_to_read = 574
# Below parameters should be in even
omron_cs_or_cj_or_cp_int_byte_size = 2
omron_cs_or_cj_or_cp_long_int_byte_size = 4
omron_cs_or_cj_or_cp_part_no_str_byte_size = 30
omron_cs_or_cj_or_cp_production_interrupt_msg_str_byte_size = 256
omron_cs_or_cj_or_cp_password_str_byte_size = 10

omron_cs_or_cj_or_cp_int_word_size = omron_cs_or_cj_or_cp_int_byte_size//2
omron_cs_or_cj_or_cp_long_int_word_size = omron_cs_or_cj_or_cp_long_int_byte_size//2
omron_cs_or_cj_or_cp_part_no_str_word_size = omron_cs_or_cj_or_cp_part_no_str_byte_size//2
omron_cs_or_cj_or_cp_production_interrupt_msg_str_word_size = omron_cs_or_cj_or_cp_production_interrupt_msg_str_byte_size//2
omron_cs_or_cj_or_cp_password_str_word_size = omron_cs_or_cj_or_cp_password_str_byte_size//2


omron_cs_or_cj_or_cp_int_zero_in_bytes = zero.to_bytes(omron_cs_or_cj_or_cp_int_byte_size, 'big')
omron_cs_or_cj_or_cp_int_one_in_bytes = one.to_bytes(omron_cs_or_cj_or_cp_int_byte_size, 'big')
omron_cs_or_cj_or_cp_int_two_in_bytes = two.to_bytes(omron_cs_or_cj_or_cp_int_byte_size, 'big')
omron_cs_or_cj_or_cp_int_three_in_bytes = three.to_bytes(omron_cs_or_cj_or_cp_int_byte_size, 'big')
omron_cs_or_cj_or_cp_int_four_in_bytes = four.to_bytes(omron_cs_or_cj_or_cp_int_byte_size, 'big')

omron_cs_or_cj_or_cp_long_int_zero_in_bytes = zero.to_bytes(omron_cs_or_cj_or_cp_long_int_byte_size, 'big')

soc_esc_data = b'X'
soc_connected_eve = threading.Event()
soc_disconnected_alarm_bytes = b'Xylem server disconnected' # should not be more than 254 bytes

no_msg_bytes = b'No messages'

def server_data_handler(soc):
    global soc_parameters_from_server_flag, soc_a000_data_pack_size_byte_len, soc_a000_where_id_byte_len, soc_a000_what_id_byte_len, soc_a000_unique_no_byte_len,\
        soc_a000_prod_data_sign, soc_a000_prod_data_sign_byte,\
        soc_a000_production_interrupt_sign, soc_a000_production_interrupt_sign_up, soc_a000_production_interrupt_sign_down, soc_a000_production_interrupt_sign_byte,\
        soc_a000_dept_passwords_sign, soc_a000_dept_passwords_sign_qa, soc_a000_dept_passwords_sign_mfg, soc_a000_dept_passwords_sign_ple, soc_a000_dept_passwords_sign_me, soc_a000_dept_passwords_sign_byte,\
        soc_a007_oee_eve_cap_sign, soc_a007_oee_eve_cap_sign_popup, soc_a007_oee_eve_cap_sign_popdown, soc_a007_oee_eve_cap_sign_byte,\
        soc_a007_manu_com_sign, soc_a007_manu_com_sign_byte,\
        soc_a007_test_oee_eve_id_chat_sign, soc_a007_test_oee_eve_id_chat_sign_byte,\
        soc_a009_process_data_sign, soc_a009_process_data_sign_ok, soc_a009_process_data_sign_nok, soc_a009_process_data_sign_byte, a000_unique_no,\
        a007_oee_hmi_popup_list, a007_oee_hmi_popdown_list, a007_manu_com_msg_with_status_dic
    parameters = soc.recv(1024)
    soc_a000_data_pack_size_byte_len = parameters[0]
    soc_a000_where_id_byte_len = parameters[1]
    soc_a000_what_id_byte_len = parameters[2]
    soc_a000_unique_no_byte_len = parameters[3]
    soc_a000_prod_data_sign = parameters[4]
    soc_a000_production_interrupt_sign = parameters[5]
    soc_a000_production_interrupt_sign_up = parameters[6]
    soc_a000_production_interrupt_sign_down = parameters[7]
    soc_a000_dept_passwords_sign = parameters[8]
    soc_a000_dept_passwords_sign_qa = parameters[9]
    soc_a000_dept_passwords_sign_mfg = parameters[10]
    soc_a000_dept_passwords_sign_ple = parameters[11]
    soc_a000_dept_passwords_sign_me = parameters[12]
    soc_a007_oee_eve_cap_sign = parameters[13]
    soc_a007_oee_eve_cap_sign_popup = parameters[14]
    soc_a007_oee_eve_cap_sign_popdown = parameters[15]
    soc_a007_manu_com_sign = parameters[16]
    soc_a007_test_oee_eve_id_chat_sign = parameters[17]
    soc_a009_process_data_sign = parameters[18]
    soc_a009_process_data_sign_ok = parameters[19]
    soc_a009_process_data_sign_nok = parameters[20]
    soc_a000_prod_data_sign_byte = soc_a000_prod_data_sign.to_bytes(1,'big')
    soc_a000_production_interrupt_sign_byte = soc_a000_production_interrupt_sign.to_bytes(1,'big')
    soc_a000_dept_passwords_sign_byte = soc_a000_dept_passwords_sign.to_bytes(1,'big')
    soc_a007_oee_eve_cap_sign_byte = soc_a007_oee_eve_cap_sign.to_bytes(1,'big')
    soc_a007_manu_com_sign_byte = soc_a007_manu_com_sign.to_bytes(1,'big')
    soc_a007_test_oee_eve_id_chat_sign_byte = soc_a007_test_oee_eve_id_chat_sign.to_bytes(1,'big')
    soc_a009_process_data_sign_byte = soc_a009_process_data_sign.to_bytes(1,'big')
    temp_byte = b''
    a007_oee_hmi_popup_list = []
    for ps in ps_list:
        temp_byte = temp_byte + ps.to_bytes(soc_a000_where_id_byte_len, 'big')
    soc.send(temp_byte)
    data_queue.put(soc.recv(1024))
    while True:
        if not server_queue.empty():
            data = server_queue.get()
        else:
            data = soc_esc_data
        soc.send(data)
        data_queue.put(soc.recv(1024))

        
def data_decode():
    global soc_parameters_from_server_flag, soc_a000_data_pack_size_byte_len, soc_a000_where_id_byte_len, soc_a000_what_id_byte_len, soc_a000_unique_no_byte_len,\
        soc_a000_prod_data_sign, soc_a000_prod_data_sign_byte,\
        soc_a000_production_interrupt_sign, soc_a000_production_interrupt_sign_up, soc_a000_production_interrupt_sign_down, soc_a000_production_interrupt_sign_byte,\
        soc_a000_dept_passwords_sign, soc_a000_dept_passwords_sign_qa, soc_a000_dept_passwords_sign_mfg, soc_a000_dept_passwords_sign_ple, soc_a000_dept_passwords_sign_me, soc_a000_dept_passwords_sign_byte,\
        soc_a007_oee_eve_cap_sign, soc_a007_oee_eve_cap_sign_popup, soc_a007_oee_eve_cap_sign_popdown, soc_a007_oee_eve_cap_sign_byte,\
        soc_a007_manu_com_sign, soc_a007_manu_com_sign_byte,\
        soc_a007_test_oee_eve_id_chat_sign, soc_a007_test_oee_eve_id_chat_sign_byte,\
        soc_a009_process_data_sign, soc_a009_process_data_sign_ok, soc_a009_process_data_sign_nok, soc_a009_process_data_sign_byte, a000_unique_no,\
        a007_oee_hmi_popup_list, a007_oee_hmi_popdown_list, a007_manu_com_msg_with_status_dic
    logged_flag = False
    while True:
        try:
            raw_data = data_queue.get()
            if raw_data == soc_esc_data:
                continue
            raw_data = bytearray(raw_data)
            while raw_data:
                sign = raw_data.pop(0)
                if sign == soc_a000_prod_data_sign:
                    a000_unique_no = int.from_bytes(raw_data[:soc_a000_unique_no_byte_len], 'big')
                    raw_data = raw_data[soc_a000_unique_no_byte_len:]
                elif sign == soc_a000_production_interrupt_sign:
                    where_id_ps = int.from_bytes(raw_data[:soc_a000_where_id_byte_len], 'big')
                    production_interrupt = raw_data[soc_a000_where_id_byte_len]
                    if production_interrupt == soc_a000_production_interrupt_sign_up:
                        msg_len = raw_data[soc_a000_where_id_byte_len+1]
                        if not xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"]:
                            xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"] = raw_data[soc_a000_where_id_byte_len+2:][:msg_len]
                        raw_data = raw_data[soc_a000_where_id_byte_len+2+msg_len:]
                    elif production_interrupt == soc_a000_production_interrupt_sign_down:
                        if xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"]:
                            xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"] = b''
                        raw_data = raw_data[soc_a000_where_id_byte_len+1:]
                elif sign == soc_a000_dept_passwords_sign:
                    where_id_ps = int.from_bytes(raw_data[:soc_a000_where_id_byte_len], 'big')
                    dept = raw_data[soc_a000_where_id_byte_len]
                    pwd_len = raw_data[soc_a000_where_id_byte_len+1]
                    if dept == soc_a000_dept_passwords_sign_qa:
                        xylem_client_dic[where_id_ps]["qa_pwd_bytes"] = raw_data[soc_a000_where_id_byte_len+2:][:pwd_len]
                    elif dept == soc_a000_dept_passwords_sign_mfg:
                        xylem_client_dic[where_id_ps]["mfg_pwd_bytes"] = raw_data[soc_a000_where_id_byte_len+2:][:pwd_len]
                    elif dept == soc_a000_dept_passwords_sign_ple:
                        xylem_client_dic[where_id_ps]["ple_pwd_bytes"] = raw_data[soc_a000_where_id_byte_len+2:][:pwd_len]
                    else:
                        xylem_client_dic[where_id_ps]["me_pwd_bytes"] = raw_data[soc_a000_where_id_byte_len+2:][:pwd_len]
                    raw_data = raw_data[soc_a000_where_id_byte_len+1+1+pwd_len:]
                elif sign == soc_a007_oee_eve_cap_sign:
                    where_id_ps = int.from_bytes(raw_data[:soc_a000_where_id_byte_len], 'big')
                    oee_eve_cap = raw_data[soc_a000_where_id_byte_len]
                    if oee_eve_cap == soc_a007_oee_eve_cap_sign_popup:
                        if not where_id_ps in a007_oee_hmi_popup_list:
                            a007_oee_hmi_popup_list.append(where_id_ps)
                    elif oee_eve_cap == soc_a007_oee_eve_cap_sign_popdown:
                        if not where_id_ps in a007_oee_hmi_popdown_list:
                            a007_oee_hmi_popdown_list.append(where_id_ps)
                    raw_data = raw_data[soc_a000_where_id_byte_len+1:]
                elif sign == soc_a007_manu_com_sign:
                    where_id_ps = int.from_bytes(raw_data[:soc_a000_where_id_byte_len], 'big')
                    msg_status = bool.from_bytes(raw_data[soc_a000_where_id_byte_len:], 'big')
                    a007_manu_com_msg_with_status_dic[where_id_ps] = msg_status
                    raw_data = raw_data[soc_a000_where_id_byte_len+1:]
            if not soc_parameters_from_server_flag:
                soc_parameters_from_server_flag = True
            if logged_flag:
                logged_flag=False
        except Exception as e:
            if  not logged_flag:
                app_log.error("Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(error_wait)


def connect_server():
    logged_flag=False
    while True:
        try:
            soc_s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            soc_s.connect((ipaddress_or_name_of_server_system,port_of_server_system))
            server_data_han = threading.Thread(target=server_data_handler, args=(soc_s,),daemon=True)
            server_data_han.start()
            while True:
                if not server_data_han.is_alive():
                    if soc_connected_eve.is_set():
                        soc_connected_eve.clear()
                    raise Exception("Socket disconnected")
                else:
                    if not soc_connected_eve.is_set():
                        soc_connected_eve.set()
                if logged_flag:
                    logged_flag=False
                time.sleep(server_thread_monitor_and_reconnect_delay)
        except Exception as e:
            soc_s.close()
            if not logged_flag:
                app_log.error("Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(error_wait)
            

def siemens_snap7_thread(ipaddress_of_plc, db_no, rack, slot, where_id_ps, a007_flag, a009_flag):
    global soc_parameters_from_server_flag, soc_a000_data_pack_size_byte_len, soc_a000_where_id_byte_len, soc_a000_what_id_byte_len, soc_a000_unique_no_byte_len,\
        soc_a000_prod_data_sign, soc_a000_prod_data_sign_byte,\
        soc_a000_production_interrupt_sign, soc_a000_production_interrupt_sign_up, soc_a000_production_interrupt_sign_down, soc_a000_production_interrupt_sign_byte,\
        soc_a000_dept_passwords_sign, soc_a000_dept_passwords_sign_qa, soc_a000_dept_passwords_sign_mfg, soc_a000_dept_passwords_sign_ple, soc_a000_dept_passwords_sign_me, soc_a000_dept_passwords_sign_byte,\
        soc_a007_oee_eve_cap_sign, soc_a007_oee_eve_cap_sign_popup, soc_a007_oee_eve_cap_sign_popdown, soc_a007_oee_eve_cap_sign_byte,\
        soc_a007_manu_com_sign, soc_a007_manu_com_sign_byte,\
        soc_a007_test_oee_eve_id_chat_sign, soc_a007_test_oee_eve_id_chat_sign_byte,\
        soc_a009_process_data_sign, soc_a009_process_data_sign_ok, soc_a009_process_data_sign_nok, soc_a009_process_data_sign_byte, a000_unique_no,\
        a007_oee_hmi_popup_list, a007_oee_hmi_popdown_list, a007_manu_com_msg_with_status_dic
    logged_flag = False
    connection_flag = False
    last_count_bytes = siemens_int_zero_in_bytes
    while True:
        try:
            if not connection_flag:
                client = snap7.client.Client()
                client.connect(ipaddress_of_plc,rack,slot)
                connection_flag=True
            plc_data = client.db_read(db_no, 0, siemens_db_total_bytes_to_read)
            if soc_connected_eve.is_set() and soc_parameters_from_server_flag:
                where_id_ps_in_bytes = where_id_ps.to_bytes(soc_a000_where_id_byte_len,'big')
                server_data = b''
                part_no_size = plc_data[siemens_db_part_no_add+1]
                part_no_in_bytes = plc_data[siemens_db_part_no_add+2:][:part_no_size]
                cc_in_bytes = plc_data[siemens_db_production_count_add:][:siemens_int_size]
                if cc_in_bytes == siemens_int_zero_in_bytes:
                    cc_in_bytes = last_count_bytes
                if not a000_unique_no is None:
                    unique_no_in_bytes = a000_unique_no.to_bytes(siemens_int_size,'big')
                    if not unique_no_in_bytes == plc_data[siemens_db_unique_no_add:][:siemens_int_size]:
                        if last_count_bytes != cc_in_bytes:
                            if last_count_bytes != siemens_int_zero_in_bytes:
                                reset = int.from_bytes(cc_in_bytes, 'big') - int.from_bytes(last_count_bytes, 'big')
                            else:
                                reset = 0
                        else:
                            reset = 0
                        client.db_write(db_no, siemens_db_unique_no_add, unique_no_in_bytes)
                        client.db_write(db_no, siemens_db_production_count_add, reset.to_bytes(siemens_int_size,'big'))
                        app_log.info(f'{where_id_ps}: Count Reset {reset}')
                        continue
                temp_byte = where_id_ps_in_bytes +\
                    part_no_size.to_bytes(1,"big") +\
                    part_no_in_bytes +\
                    siemens_int_size.to_bytes(1, "big") +\
                    cc_in_bytes
                server_data = server_data +\
                    soc_a000_prod_data_sign_byte +\
                    len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                    temp_byte
                if xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"]:
                    if int.from_bytes(plc_data[siemens_db_production_interrupt_add:][:siemens_int_size], 'big') != 1 :
                        client.db_write(db_no, siemens_db_production_interrupt_add, siemens_int_one_in_bytes)
                        print("msg writed0")
                    production_interrupt_msg_occu_len = plc_data[siemens_db_production_interrupt_msg_add+1]
                    if plc_data[siemens_db_production_interrupt_msg_add+2:][:production_interrupt_msg_occu_len] != xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"]:
                        if production_interrupt_msg_occu_len:
                            client.db_write(db_no, siemens_db_production_interrupt_msg_add+1, bytearray(production_interrupt_msg_occu_len+1))
                        client.db_write(db_no, siemens_db_production_interrupt_msg_add+1,\
                            len(xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"]).to_bytes(1, 'big') +\
                            xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"])
                        print("msg writed1")
                else:
                    if int.from_bytes(plc_data[siemens_db_production_interrupt_add:][:siemens_int_size], 'big'):
                        client.db_write(db_no, siemens_db_production_interrupt_add, siemens_int_zero_in_bytes)
                        print("msg writed2")
                    production_interrupt_msg_occu_len = plc_data[siemens_db_production_interrupt_msg_add+1]
                    if plc_data[siemens_db_production_interrupt_msg_add+2:][:production_interrupt_msg_occu_len] != xylem_client_dic[where_id_ps]["prod_interrupt_msg_default_bytes"]:
                        if production_interrupt_msg_occu_len:
                            client.db_write(db_no, siemens_db_production_interrupt_msg_add+1, bytearray(production_interrupt_msg_occu_len+1))
                        client.db_write(db_no, siemens_db_production_interrupt_msg_add+1,\
                            len(xylem_client_dic[where_id_ps]["prod_interrupt_msg_default_bytes"]).to_bytes(1, 'big') +\
                            xylem_client_dic[where_id_ps]["prod_interrupt_msg_default_bytes"])
                        print("msg writed11")
                pwd_occu_len = plc_data[siemens_db_qa_password_add+1]
                if plc_data[siemens_db_qa_password_add+2:][:pwd_occu_len] != xylem_client_dic[where_id_ps]["qa_pwd_bytes"]:
                    if pwd_occu_len:
                        client.db_write(db_no, siemens_db_qa_password_add+1, bytearray(pwd_occu_len+1))
                    client.db_write(db_no, siemens_db_qa_password_add+1,
                        len(xylem_client_dic[where_id_ps]["qa_pwd_bytes"]).to_bytes(1, 'big') +\
                        xylem_client_dic[where_id_ps]["qa_pwd_bytes"]
                    )
                    print("msg writed4")
                pwd_occu_len = plc_data[siemens_db_mfg_password_add+1]
                if plc_data[siemens_db_mfg_password_add+2:][:pwd_occu_len] != xylem_client_dic[where_id_ps]["mfg_pwd_bytes"]:
                    if pwd_occu_len:
                        client.db_write(db_no, siemens_db_mfg_password_add+1, bytearray(pwd_occu_len+1))
                    client.db_write(db_no, siemens_db_mfg_password_add+1,
                        len(xylem_client_dic[where_id_ps]["mfg_pwd_bytes"]).to_bytes(1, 'big') +\
                        xylem_client_dic[where_id_ps]["mfg_pwd_bytes"]
                    )
                    print("msg writed5")
                pwd_occu_len = plc_data[siemens_db_ple_password_add+1]
                if plc_data[siemens_db_ple_password_add+2:][:pwd_occu_len] != xylem_client_dic[where_id_ps]["ple_pwd_bytes"]:
                    if pwd_occu_len:
                        client.db_write(db_no, siemens_db_ple_password_add+1, bytearray(pwd_occu_len+1))
                    client.db_write(db_no, siemens_db_ple_password_add+1,
                        len(xylem_client_dic[where_id_ps]["ple_pwd_bytes"]).to_bytes(1, 'big') +\
                        xylem_client_dic[where_id_ps]["ple_pwd_bytes"]
                    )
                    print("msg writed6")
                pwd_occu_len = plc_data[siemens_db_me_password_add+1]
                if plc_data[siemens_db_me_password_add+2:][:pwd_occu_len] != xylem_client_dic[where_id_ps]["me_pwd_bytes"]:
                    if pwd_occu_len:
                        client.db_write(db_no, siemens_db_me_password_add+1, bytearray(pwd_occu_len+1))
                    client.db_write(db_no, siemens_db_me_password_add+1,
                        len(xylem_client_dic[where_id_ps]["me_pwd_bytes"]).to_bytes(1, 'big') +\
                        xylem_client_dic[where_id_ps]["me_pwd_bytes"]
                    )
                    print("msg writed7")
                if a007_flag:
                    if where_id_ps in a007_oee_hmi_popup_list:
                        if not int.from_bytes(plc_data[siemens_db_oee_interrupt_add:][:siemens_int_size], 'big') == 1:
                            client.db_write(db_no, siemens_db_oee_interrupt_add, siemens_int_one_in_bytes)
                        else:
                            if int.from_bytes(plc_data[siemens_db_oee_data_ready_add:][:siemens_int_size], 'big') == 1:
                                oee_eve_where_id = int.from_bytes(plc_data[siemens_db_oee_where_id_add:][:siemens_long_int_size], 'big')
                                oee_eve_what_id = int.from_bytes(plc_data[siemens_db_oee_what_id_add:][:siemens_long_int_size], 'big')
                                temp_byte = where_id_ps_in_bytes +\
                                    oee_eve_where_id.to_bytes(soc_a000_where_id_byte_len, 'big') +\
                                    oee_eve_what_id.to_bytes(soc_a000_what_id_byte_len, 'big')
                                server_data = server_data +\
                                    soc_a007_oee_eve_cap_sign_byte +\
                                    len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                                    temp_byte
                                client.db_write(db_no, siemens_db_oee_where_id_add, siemens_long_int_zero_in_bytes)
                                client.db_write(db_no, siemens_db_oee_what_id_add, siemens_long_int_zero_in_bytes)
                                client.db_write(db_no, siemens_db_oee_data_ready_add, siemens_int_zero_in_bytes)
                                client.db_write(db_no, siemens_db_oee_interrupt_add, siemens_int_zero_in_bytes)
                                a007_oee_hmi_popup_list.remove(where_id_ps)
                    else:
                        if int.from_bytes(plc_data[siemens_db_oee_interrupt_add:][:siemens_int_size], 'big'):
                            client.db_write(db_no, siemens_db_oee_interrupt_add, siemens_int_zero_in_bytes)
                        if int.from_bytes(plc_data[siemens_db_oee_data_ready_add:][:siemens_int_size], 'big') == 1:
                            oee_eve_where_id = int.from_bytes(plc_data[siemens_db_oee_where_id_add:][:siemens_long_int_size], 'big')
                            oee_eve_what_id = int.from_bytes(plc_data[siemens_db_oee_what_id_add:][:siemens_long_int_size], 'big')
                            temp_byte = where_id_ps_in_bytes +\
                                oee_eve_where_id.to_bytes(soc_a000_where_id_byte_len, 'big') +\
                                oee_eve_what_id.to_bytes(soc_a000_what_id_byte_len, 'big')
                            server_data = server_data +\
                                soc_a007_test_oee_eve_id_chat_sign_byte +\
                                len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                                temp_byte
                            client.db_write(db_no, siemens_db_oee_where_id_add, siemens_long_int_zero_in_bytes)
                            client.db_write(db_no, siemens_db_oee_what_id_add, siemens_long_int_zero_in_bytes)
                            client.db_write(db_no, siemens_db_oee_data_ready_add, siemens_int_zero_in_bytes)
                    if where_id_ps in a007_oee_hmi_popdown_list:
                        client.db_write(db_no, siemens_db_oee_interrupt_add, siemens_int_two_in_bytes)
                        if where_id_ps in a007_oee_hmi_popup_list:
                            a007_oee_hmi_popup_list.remove(where_id_ps)
                        a007_oee_hmi_popdown_list.remove(where_id_ps)
                    if int.from_bytes(plc_data[siemens_db_manu_com_avl_add:][:siemens_int_size], 'big') == 1:
                        manu_com_where_id = int.from_bytes(plc_data[siemens_db_manu_com_where_id_add:][:siemens_long_int_size], 'big')
                        manu_com_what_id = int.from_bytes(plc_data[siemens_db_manu_com_what_id_add:][:siemens_long_int_size], 'big')
                        temp_byte = where_id_ps_in_bytes +\
                            manu_com_where_id.to_bytes(soc_a000_where_id_byte_len, 'big') +\
                            manu_com_what_id.to_bytes(soc_a000_what_id_byte_len, 'big')
                        server_data = server_data +\
                            soc_a007_manu_com_sign_byte +\
                            len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                            temp_byte
                        client.db_write(db_no, siemens_db_manu_com_avl_add, siemens_int_two_in_bytes)
                        client.db_write(db_no, siemens_db_manu_com_where_id_add, siemens_long_int_zero_in_bytes)
                        client.db_write(db_no, siemens_db_manu_com_what_id_add, siemens_long_int_zero_in_bytes)
                    if where_id_ps in a007_manu_com_msg_with_status_dic:
                        if a007_manu_com_msg_with_status_dic[where_id_ps]:
                            client.db_write(db_no, siemens_db_manu_com_avl_add, siemens_int_three_in_bytes)
                        else:
                            client.db_write(db_no, siemens_db_manu_com_avl_add, siemens_int_four_in_bytes)
                        del a007_manu_com_msg_with_status_dic[where_id_ps]
                if a009_flag:
                    temp_str1="barcode data 1"
                    temp_str2="barcode data 2"
                    temp_byte = where_id_ps_in_bytes +\
                        len(temp_str1).to_bytes(1, 'big') +\
                        temp_str1.encode() +\
                        len(temp_str2).to_bytes(1, 'big') +\
                        temp_str2.encode()
                    server_data = server_data +\
                        soc_a009_process_data_sign +\
                        len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                        temp_byte
                if server_queue.full():
                    server_queue.get()
                server_queue.put(server_data)
                last_count_bytes = cc_in_bytes
            else:
                if int.from_bytes(plc_data[siemens_db_production_interrupt_add:][:siemens_int_size], 'big') != 1 :
                    client.db_write(db_no, siemens_db_production_interrupt_add, siemens_int_one_in_bytes)
                    print("msg writed8")
                production_interrupt_msg_occu_len = plc_data[siemens_db_production_interrupt_msg_add+1]
                if plc_data[siemens_db_production_interrupt_msg_add+2:][:production_interrupt_msg_occu_len] != soc_disconnected_alarm_bytes:
                    if production_interrupt_msg_occu_len:
                        client.db_write(db_no, siemens_db_production_interrupt_msg_add+1, bytearray(production_interrupt_msg_occu_len+1))
                    client.db_write(db_no, siemens_db_production_interrupt_msg_add+1,\
                    len(soc_disconnected_alarm_bytes).to_bytes(1, 'big') +\
                    soc_disconnected_alarm_bytes)
                    print("msg writed9")
            client.db_write(db_no, siemens_db_software_beat_add, siemens_int_one_in_bytes)
            time.sleep(siemens_plc_db_read_delay)
            if logged_flag:
                logged_flag=False
        except Exception as e:
            if str(e)=="b' TCP : Unreachable peer'":
                print(f'SST{where_id_ps}: Unable to connect')
                connection_flag=False
            if str(e)=="b' ISO : An error occurred during send TCP : Connection reset by peer'":
                print(f'SST{where_id_ps}: Disconnected')
                connection_flag=False
            if str(e)=="b' ISO : An error occurred during recv TCP : Connection timed out'":
                print(f'SST{where_id_ps}: Unable  to connect')
                connection_flag=False
            if not logged_flag:
                app_log.error(f"{where_id_ps}: Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(error_wait)


def get_int_from_double_word_bytes(bytes_data: bytes):
    word1 = int.from_bytes(bytes_data[:2], byteorder='big')
    word2 = int.from_bytes(bytes_data[2:], byteorder='big')
    return (word2 << 16) + word1


def get_bytes_from_reverse_word_order(data: bytes):
    temp_str=data.decode().strip()
    len_temp_str=len(temp_str)
    temp_string=''
    for i in range(0,len_temp_str,2):
        if not len_temp_str==i+1:
            temp_string=temp_string+temp_str[i+1]
        temp_string=temp_string+temp_str[i]
    temp_string=temp_string.strip('\x00').strip()
    return temp_string.encode()


def get_stripped_bytes(bytes_data):
    return bytes_data.strip(b'\x00')


def omron_fins_thread(ipaddress_of_plc, dest_node, srce_node, start_word_add, where_id_ps, a007_flag, a009_flag):
    global soc_parameters_from_server_flag, soc_a000_data_pack_size_byte_len, soc_a000_where_id_byte_len, soc_a000_what_id_byte_len, soc_a000_unique_no_byte_len,\
        soc_a000_prod_data_sign, soc_a000_prod_data_sign_byte,\
        soc_a000_production_interrupt_sign, soc_a000_production_interrupt_sign_up, soc_a000_production_interrupt_sign_down, soc_a000_production_interrupt_sign_byte,\
        soc_a000_dept_passwords_sign, soc_a000_dept_passwords_sign_qa, soc_a000_dept_passwords_sign_mfg, soc_a000_dept_passwords_sign_ple, soc_a000_dept_passwords_sign_me, soc_a000_dept_passwords_sign_byte,\
        soc_a007_oee_eve_cap_sign, soc_a007_oee_eve_cap_sign_popup, soc_a007_oee_eve_cap_sign_popdown, soc_a007_oee_eve_cap_sign_byte,\
        soc_a007_manu_com_sign, soc_a007_manu_com_sign_byte,\
        soc_a007_test_oee_eve_id_chat_sign, soc_a007_test_oee_eve_id_chat_sign_byte,\
        soc_a009_process_data_sign, soc_a009_process_data_sign_ok, soc_a009_process_data_sign_nok, soc_a009_process_data_sign_byte, a000_unique_no,\
        a007_oee_hmi_popup_list, a007_oee_hmi_popdown_list, a007_manu_com_msg_with_status_dic
    logged_flag = False
    last_count_bytes = omron_cs_or_cj_or_cp_int_zero_in_bytes
    start_word_add_bytes = start_word_add.to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_software_beat_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_software_beat_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_part_no_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_part_no_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_unique_no_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_unique_no_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_production_count_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_production_count_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_oee_interrupt_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_oee_interrupt_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_production_interrupt_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_production_interrupt_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_production_interrupt_msg_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_production_interrupt_msg_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_oee_data_ready_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_oee_data_ready_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_oee_where_id_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_oee_where_id_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_oee_what_id_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_oee_what_id_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_qa_password_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_qa_password_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_mfg_password_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_mfg_password_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_ple_password_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_ple_password_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_me_password_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_me_password_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_manu_com_avl_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_manu_com_avl_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_manu_com_where_id_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_manu_com_where_id_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_manu_com_what_id_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_manu_com_what_id_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_ftr_data_avl_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_ftr_data_avl_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_barcode_1_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_barcode_1_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_barcode_2_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_barcode_2_byte_add//2).to_bytes(2,'big')+b'\x00'
    omron_cs_or_cj_or_cp_cycle_status_word_add_bytes = (start_word_add + omron_cs_or_cj_or_cp_cycle_status_byte_add//2).to_bytes(2,'big')+b'\x00'
    while True:
        try:
            fins_instance = fins.udp.UDPFinsConnection()
            fins_instance.connect(ipaddress_of_plc,9600,0)
            fins_instance.dest_node_add=dest_node
            fins_instance.srce_node_add=srce_node
            while True:
                plc_data = fins_instance.memory_area_read(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD, start_word_add_bytes, omron_cs_or_cj_or_cp_total_words_to_read)[14:]
                if soc_connected_eve.is_set() and soc_parameters_from_server_flag:
                    where_id_ps_in_bytes = where_id_ps.to_bytes(soc_a000_where_id_byte_len,'big')
                    server_data = b''
                    part_no_in_bytes = get_bytes_from_reverse_word_order(plc_data[omron_cs_or_cj_or_cp_part_no_byte_add:][:omron_cs_or_cj_or_cp_part_no_str_byte_size])
                    cc_in_bytes = plc_data[omron_cs_or_cj_or_cp_production_count_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size]
                    if not a000_unique_no is None:
                        unique_no_in_bytes = a000_unique_no.to_bytes(omron_cs_or_cj_or_cp_int_byte_size,'big')
                        if not unique_no_in_bytes == plc_data[omron_cs_or_cj_or_cp_unique_no_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size]:
                            if last_count_bytes != cc_in_bytes:
                                if last_count_bytes != omron_cs_or_cj_or_cp_int_zero_in_bytes:
                                    reset = int.from_bytes(cc_in_bytes, 'big') - int.from_bytes(last_count_bytes, 'big')
                                else:
                                    reset = 0
                            else:
                                reset = 0
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_unique_no_word_add_bytes,unique_no_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_production_count_word_add_bytes,reset.to_bytes(omron_cs_or_cj_or_cp_int_byte_size,'big'),omron_cs_or_cj_or_cp_int_word_size)
                            app_log.info(f'{where_id_ps}: Count Reset {reset}')
                            continue
                    temp_byte = where_id_ps_in_bytes +\
                        len(part_no_in_bytes).to_bytes(1,'big') +\
                        part_no_in_bytes +\
                        omron_cs_or_cj_or_cp_int_byte_size.to_bytes(1, "big") +\
                        cc_in_bytes
                    server_data = server_data +\
                        soc_a000_prod_data_sign_byte +\
                        len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                        temp_byte
                    if xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"]:
                        if int.from_bytes(plc_data[omron_cs_or_cj_or_cp_production_interrupt_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size], 'big') != 1 :
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_production_interrupt_word_add_bytes,omron_cs_or_cj_or_cp_int_one_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            print("msg writed0")
                        production_interrupt_msg_in_bytes = get_stripped_bytes(plc_data[omron_cs_or_cj_or_cp_production_interrupt_msg_byte_add:][:omron_cs_or_cj_or_cp_production_interrupt_msg_str_byte_size])
                        if production_interrupt_msg_in_bytes != xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"]:
                            temp_bytes = xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"] + bytearray(omron_cs_or_cj_or_cp_production_interrupt_msg_str_byte_size-len(xylem_client_dic[where_id_ps]["prod_interrupt_msg_bytes"]))
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_production_interrupt_msg_word_add_bytes,temp_bytes,omron_cs_or_cj_or_cp_production_interrupt_msg_str_word_size)
                            print("msg writed1")
                    else:
                        if int.from_bytes(plc_data[omron_cs_or_cj_or_cp_production_interrupt_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size], 'big'):
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_production_interrupt_word_add_bytes,omron_cs_or_cj_or_cp_int_zero_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            print("msg writed2")
                        production_interrupt_msg_in_bytes = get_stripped_bytes(plc_data[omron_cs_or_cj_or_cp_production_interrupt_msg_byte_add:][:omron_cs_or_cj_or_cp_production_interrupt_msg_str_byte_size])
                        if production_interrupt_msg_in_bytes != xylem_client_dic[where_id_ps]["prod_interrupt_msg_default_bytes"]:
                            temp_bytes = xylem_client_dic[where_id_ps]["prod_interrupt_msg_default_bytes"] + bytearray(omron_cs_or_cj_or_cp_production_interrupt_msg_str_byte_size-len(xylem_client_dic[where_id_ps]["prod_interrupt_msg_default_bytes"]))
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_production_interrupt_msg_word_add_bytes,temp_bytes,omron_cs_or_cj_or_cp_production_interrupt_msg_str_word_size)
                            print("msg writed11")
                    qa_pwd_in_bytes = get_stripped_bytes(plc_data[omron_cs_or_cj_or_cp_qa_password_byte_add:][:omron_cs_or_cj_or_cp_password_str_byte_size])
                    if qa_pwd_in_bytes != xylem_client_dic[where_id_ps]["qa_pwd_bytes"]:
                        temp_bytes = xylem_client_dic[where_id_ps]["qa_pwd_bytes"] + bytearray(omron_cs_or_cj_or_cp_password_str_byte_size-len(xylem_client_dic[where_id_ps]["qa_pwd_bytes"]))
                        fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_qa_password_word_add_bytes,temp_bytes,omron_cs_or_cj_or_cp_password_str_word_size)
                        print("msg writed4")
                    mfg_pwd_in_bytes = get_stripped_bytes(plc_data[omron_cs_or_cj_or_cp_mfg_password_byte_add:][:omron_cs_or_cj_or_cp_password_str_byte_size])
                    if mfg_pwd_in_bytes != xylem_client_dic[where_id_ps]["mfg_pwd_bytes"]:
                        temp_bytes = xylem_client_dic[where_id_ps]["mfg_pwd_bytes"] + bytearray(omron_cs_or_cj_or_cp_password_str_byte_size-len(xylem_client_dic[where_id_ps]["mfg_pwd_bytes"]))
                        fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_mfg_password_word_add_bytes,temp_bytes,omron_cs_or_cj_or_cp_password_str_word_size)
                        print("msg writed5")
                    ple_pwd_in_bytes = get_stripped_bytes(plc_data[omron_cs_or_cj_or_cp_ple_password_byte_add:][:omron_cs_or_cj_or_cp_password_str_byte_size])
                    if ple_pwd_in_bytes != xylem_client_dic[where_id_ps]["ple_pwd_bytes"]:
                        temp_bytes = xylem_client_dic[where_id_ps]["ple_pwd_bytes"] + bytearray(omron_cs_or_cj_or_cp_password_str_byte_size-len(xylem_client_dic[where_id_ps]["ple_pwd_bytes"]))
                        fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_ple_password_word_add_bytes,temp_bytes,omron_cs_or_cj_or_cp_password_str_word_size)
                        print("msg writed6")
                    me_pwd_in_bytes = get_stripped_bytes(plc_data[omron_cs_or_cj_or_cp_me_password_byte_add:][:omron_cs_or_cj_or_cp_password_str_byte_size])
                    if me_pwd_in_bytes != xylem_client_dic[where_id_ps]["me_pwd_bytes"]:
                        temp_bytes = xylem_client_dic[where_id_ps]["me_pwd_bytes"] + bytearray(omron_cs_or_cj_or_cp_password_str_byte_size-len(xylem_client_dic[where_id_ps]["me_pwd_bytes"]))
                        fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_me_password_word_add_bytes,temp_bytes,omron_cs_or_cj_or_cp_password_str_word_size)
                        print("msg writed7")
                    if a007_flag:
                        if where_id_ps in a007_oee_hmi_popup_list:
                            if not int.from_bytes(plc_data[omron_cs_or_cj_or_cp_oee_interrupt_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size], 'big') == 1:
                                fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_interrupt_word_add_bytes,omron_cs_or_cj_or_cp_int_one_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            else:
                                if int.from_bytes(plc_data[omron_cs_or_cj_or_cp_oee_data_ready_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size], 'big') == 1:
                                    oee_eve_where_id = get_int_from_double_word_bytes(plc_data[omron_cs_or_cj_or_cp_oee_where_id_byte_add:][:omron_cs_or_cj_or_cp_long_int_byte_size])
                                    oee_eve_what_id = get_int_from_double_word_bytes(plc_data[omron_cs_or_cj_or_cp_oee_what_id_byte_add:][:omron_cs_or_cj_or_cp_long_int_byte_size])
                                    temp_byte = where_id_ps_in_bytes +\
                                        oee_eve_where_id.to_bytes(soc_a000_where_id_byte_len, 'big') +\
                                        oee_eve_what_id.to_bytes(soc_a000_what_id_byte_len, 'big')
                                    server_data = server_data +\
                                        soc_a007_oee_eve_cap_sign_byte +\
                                        len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                                        temp_byte
                                    fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_where_id_word_add_bytes,omron_cs_or_cj_or_cp_long_int_zero_in_bytes,omron_cs_or_cj_or_cp_long_int_word_size)
                                    fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_what_id_word_add_bytes,omron_cs_or_cj_or_cp_long_int_zero_in_bytes,omron_cs_or_cj_or_cp_long_int_word_size)
                                    fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_data_ready_word_add_bytes,omron_cs_or_cj_or_cp_int_zero_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                                    fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_interrupt_word_add_bytes,omron_cs_or_cj_or_cp_int_zero_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                                    a007_oee_hmi_popup_list.remove(where_id_ps)
                        else:
                            if int.from_bytes(plc_data[omron_cs_or_cj_or_cp_oee_interrupt_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size], 'big'):
                                fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_interrupt_word_add_bytes,omron_cs_or_cj_or_cp_int_zero_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            if int.from_bytes(plc_data[omron_cs_or_cj_or_cp_oee_data_ready_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size], 'big') == 1:
                                oee_eve_where_id = get_int_from_double_word_bytes(plc_data[omron_cs_or_cj_or_cp_oee_where_id_byte_add:][:omron_cs_or_cj_or_cp_long_int_byte_size])
                                oee_eve_what_id = get_int_from_double_word_bytes(plc_data[omron_cs_or_cj_or_cp_oee_what_id_byte_add:][:omron_cs_or_cj_or_cp_long_int_byte_size])
                                temp_byte = where_id_ps_in_bytes +\
                                    oee_eve_where_id.to_bytes(soc_a000_where_id_byte_len, 'big') +\
                                    oee_eve_what_id.to_bytes(soc_a000_what_id_byte_len, 'big')
                                server_data = server_data +\
                                    soc_a007_test_oee_eve_id_chat_sign_byte +\
                                    len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                                    temp_byte
                                fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_where_id_word_add_bytes,omron_cs_or_cj_or_cp_long_int_zero_in_bytes,omron_cs_or_cj_or_cp_long_int_word_size)
                                fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_what_id_word_add_bytes,omron_cs_or_cj_or_cp_long_int_zero_in_bytes,omron_cs_or_cj_or_cp_long_int_word_size)
                                fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_data_ready_word_add_bytes,omron_cs_or_cj_or_cp_int_zero_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                        if where_id_ps in a007_oee_hmi_popdown_list:
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_oee_interrupt_word_add_bytes,omron_cs_or_cj_or_cp_int_two_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            if where_id_ps in a007_oee_hmi_popup_list:
                                a007_oee_hmi_popup_list.remove(where_id_ps)
                            a007_oee_hmi_popdown_list.remove(where_id_ps)
                        if int.from_bytes(plc_data[omron_cs_or_cj_or_cp_manu_com_avl_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size], 'big') == 1:
                            manu_com_where_id = get_int_from_double_word_bytes(plc_data[omron_cs_or_cj_or_cp_manu_com_where_id_byte_add:][:omron_cs_or_cj_or_cp_long_int_byte_size])
                            manu_com_what_id = get_int_from_double_word_bytes(plc_data[omron_cs_or_cj_or_cp_manu_com_what_id_byte_add:][:omron_cs_or_cj_or_cp_long_int_byte_size])
                            temp_byte = where_id_ps_in_bytes +\
                                manu_com_where_id.to_bytes(soc_a000_where_id_byte_len, 'big') +\
                                manu_com_what_id.to_bytes(soc_a000_what_id_byte_len, 'big')
                            server_data = server_data +\
                                soc_a007_manu_com_sign_byte +\
                                len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                                temp_byte
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_manu_com_avl_word_add_bytes,omron_cs_or_cj_or_cp_int_two_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_manu_com_where_id_word_add_bytes,omron_cs_or_cj_or_cp_long_int_zero_in_bytes,omron_cs_or_cj_or_cp_long_int_word_size)
                            fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_manu_com_what_id_word_add_bytes,omron_cs_or_cj_or_cp_long_int_zero_in_bytes,omron_cs_or_cj_or_cp_long_int_word_size)
                        if where_id_ps in a007_manu_com_msg_with_status_dic:
                            if a007_manu_com_msg_with_status_dic[where_id_ps]:
                                fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_manu_com_avl_word_add_bytes,omron_cs_or_cj_or_cp_int_three_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            else:
                                fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_manu_com_avl_word_add_bytes,omron_cs_or_cj_or_cp_int_four_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                            del a007_manu_com_msg_with_status_dic[where_id_ps]
                    if a009_flag:
                        temp_str1="barcode data 1"
                        temp_str2="barcode data 2"
                        temp_byte = where_id_ps_in_bytes +\
                            len(temp_str1).to_bytes(1, 'big') +\
                            temp_str1.encode() +\
                            len(temp_str2).to_bytes(1, 'big') +\
                            temp_str2.encode()
                        server_data = server_data +\
                            soc_a009_process_data_sign +\
                            len(temp_byte).to_bytes(soc_a000_data_pack_size_byte_len, 'big') +\
                            temp_byte
                    if server_queue.full():
                        server_queue.get()
                    server_queue.put(server_data)
                    last_count_bytes = cc_in_bytes
                else:
                    if int.from_bytes(plc_data[omron_cs_or_cj_or_cp_production_interrupt_byte_add:][:omron_cs_or_cj_or_cp_int_byte_size], 'big') != 1 :
                        fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_production_interrupt_word_add_bytes,omron_cs_or_cj_or_cp_int_one_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                        print("msg writed8")
                    production_interrupt_msg_in_bytes = get_stripped_bytes(plc_data[omron_cs_or_cj_or_cp_production_interrupt_msg_byte_add:][:omron_cs_or_cj_or_cp_production_interrupt_msg_str_byte_size])
                    if production_interrupt_msg_in_bytes != soc_disconnected_alarm_bytes:
                        temp_bytes = soc_disconnected_alarm_bytes + bytearray(omron_cs_or_cj_or_cp_production_interrupt_msg_str_byte_size-len(soc_disconnected_alarm_bytes))
                        fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_production_interrupt_msg_word_add_bytes,temp_bytes,omron_cs_or_cj_or_cp_production_interrupt_msg_str_word_size)
                        print("msg writed9")
                fins_instance.memory_area_write(fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD,omron_cs_or_cj_or_cp_software_beat_word_add_bytes,omron_cs_or_cj_or_cp_int_one_in_bytes,omron_cs_or_cj_or_cp_int_word_size)
                time.sleep(omron_CS_or_CJ_or_CP_plc_data_read_delay)
                if logged_flag:
                    logged_flag=False
        except Exception as e:
            if not logged_flag:
                app_log.error(f"{where_id_ps}: Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(error_wait)


if ipaddresses_of_siemens_plc[0]:    
    for index_i, ip in enumerate(ipaddresses_of_siemens_plc):
        where_id_ps = int(where_id_ps_for_siemens_plc[index_i])
        threading.Thread(target = siemens_snap7_thread,
            args=(
                ip,
                int(db_numbers_of_siemens_plc_respectively[index_i]),
                int(rack_numbers_of_siemens_plc_respectively[index_i]),
                int(slot_numbers_of_siemens_plc_respectively[index_i]),
                where_id_ps,
                eval(is_this_a_production_station_of_siemens_plc_for_a007_oee_monitoring[index_i].strip().lower().capitalize()),
                eval(is_this_a_production_station_of_siemens_plc_for_a009_process_ftr[index_i].strip().lower().capitalize()),
            ),
            daemon = True
        ).start()
        xylem_client_dic[where_id_ps] = sub_dict_default.copy()
        xylem_client_dic[where_id_ps]["prod_interrupt_msg_default_bytes"] = no_msg_bytes
        app_log.info(f'Siemens_snap7_thread started {where_id_ps}')
else:
    app_log.info(f'No Siemens_snap7_thread started')

if ipaddresses_of_omron_CS_or_CJ_or_CP_plc[0]:    
    for index_i, ip in enumerate(ipaddresses_of_omron_CS_or_CJ_or_CP_plc):
        where_id_ps = int(where_id_ps_for_omron_CS_or_CJ_or_CP_plc[index_i])
        threading.Thread(target = omron_fins_thread,
            args=(
                ip,
                int(destination_nodes_of_omron_CS_or_CJ_or_CP_plc[index_i]),
                int(source_nodes_of_omron_CS_or_CJ_or_CP_plc[index_i]),
                int(start_word_addresses_of_omron_CS_or_CJ_or_CP_plc[index_i]),
                where_id_ps,
                eval(is_this_a_production_station_of_omron_CS_or_CJ_or_CP_plc_for_a007_oee_monitoring[index_i].strip().lower().capitalize()),
                eval(is_this_a_production_station_of_omron_CS_or_CJ_or_CP_plc_for_a009_process_ftr[index_i].strip().lower().capitalize()),
            ),
            daemon = True
        ).start()
        xylem_client_dic[where_id_ps] = sub_dict_default.copy()
        xylem_client_dic[where_id_ps]["prod_interrupt_msg_default_bytes"] = no_msg_bytes
        app_log.info(f'Omron_fins_thread started {where_id_ps}')
else:
    app_log.info(f'No Omron_fins_thread started')

threading.Thread(target = connect_server, daemon = True).start()
threading.Thread(target = data_decode, daemon = True).start()

while True:
    time.sleep(60)