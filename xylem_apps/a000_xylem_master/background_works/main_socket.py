import json, socket, time, datetime, queue, requests, schedule, copy, textwrap, logging
from django.db.utils import ProgrammingError

from xylem.settings import XYLEM_MODE, XYLEM_MODE_DIC
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import SocketWhereIDs

a000_bw_logger = logging.getLogger(serve.Apps.A000XylemMaster.bw_logger_name)

data_spliter_to_apps_queue = queue.Queue(maxsize=30)
data_spliter_to_clients_queue = queue.Queue(maxsize=30)
maintenance_chat_queue = queue.Queue(maxsize=30)

a004_app_to_client_queue = queue.Queue(maxsize=30)
a007_app_to_client_queue = queue.Queue(maxsize=30)
a007_client_to_app_queue = queue.Queue(maxsize=30)
a009_app_to_client_queue = queue.Queue(maxsize=30)
a009_client_to_app_queue = queue.Queue(maxsize=30)
app_to_client_queues_dic = {
    a004_app_to_client_queue: [],
    a007_app_to_client_queue: [],
    a009_app_to_client_queue: []
}
client_to_app_queues_dic = {
    a007_client_to_app_queue:[
        serve.soc_a000_prod_data_sign,
        serve.soc_a007_oee_eve_cap_sign,
        serve.soc_a007_manu_com_sign,
        serve.soc_a007_test_oee_eve_id_chat_sign
    ],
    a009_client_to_app_queue:[
        serve.soc_a009_process_data_sign,
    ]
}

# send_data_queue: queue of sending to client , data_last_recv_time : time of last data recevied, soc_connection: socket connection status,\
# ps_connection: production station connection status, ma_trig_delay: maintenance alert trigger delay,
sub_dict_default = {
    "send_data_queue" : b'', "data_last_recv_time": None, "soc_connection": None, "ps_connection": None, "ma_trig_delay": None,
}
communication_dict = {} # only to read import
a000_unique_no_in_bytes = None

soc_esc_data = b'X'


def update_a000_unique_no():
    global a000_unique_no_in_bytes
    a000_unique_no = int(datetime.datetime.now().strftime('%m%d'))
    a000_unique_no_in_bytes = a000_unique_no.to_bytes(serve.soc_a000_unique_no_byte_len,'big')


def client_handler(connection):
    global a000_unique_no_in_bytes
    client_where_id_list = []
    temp_byte = serve.soc_a000_data_pack_size_byte_len_byte +\
        serve.soc_a000_where_id_byte_len_byte +\
        serve.soc_a000_what_id_byte_len_byte +\
        serve.soc_a000_unique_no_byte_len_byte +\
        serve.soc_a000_prod_data_sign_byte +\
        serve.soc_a000_production_interrupt_sign_byte +\
        serve.soc_a000_production_interrupt_sign_up_byte +\
        serve.soc_a000_production_interrupt_sign_down_byte +\
        serve.soc_a000_dept_passwords_sign_byte +\
        serve.soc_a000_dept_passwords_sign_qa_byte +\
        serve.soc_a000_dept_passwords_sign_mfg_byte +\
        serve.soc_a000_dept_passwords_sign_ple_byte +\
        serve.soc_a000_dept_passwords_sign_me_byte +\
        serve.soc_a007_oee_eve_cap_sign_byte +\
        serve.soc_a007_oee_eve_cap_sign_popup_byte +\
        serve.soc_a007_oee_eve_cap_sign_popdown_byte +\
        serve.soc_a007_manu_com_sign_byte +\
        serve.soc_a007_test_oee_eve_id_chat_sign_byte +\
        serve.soc_a009_process_data_sign_byte +\
        serve.soc_a009_process_data_sign_ok_byte +\
        serve.soc_a009_process_data_sign_nok_byte
    connection.send(temp_byte)
    client_data = connection.recv(1024)
    temp_byte = b''
    while client_data:
        where_id = int.from_bytes(client_data[:serve.soc_a000_where_id_byte_len], 'big')
        client_where_id_list.append(where_id)
        communication_dict[where_id]["soc_connection"] = True

        temp_byte = temp_byte +\
        serve.soc_a000_dept_passwords_sign_byte +\
        client_data[:serve.soc_a000_where_id_byte_len] +\
        serve.soc_a000_dept_passwords_sign_qa_byte +\
        len(serve.a000_qa_password).to_bytes(1, 'big') +\
        serve.a000_qa_password.encode()

        temp_byte = temp_byte +\
        serve.soc_a000_dept_passwords_sign_byte +\
        client_data[:serve.soc_a000_where_id_byte_len] +\
        serve.soc_a000_dept_passwords_sign_mfg_byte +\
        len(serve.a000_mfg_password).to_bytes(1, 'big') +\
        serve.a000_mfg_password.encode()

        temp_byte = temp_byte +\
        serve.soc_a000_dept_passwords_sign_byte +\
        client_data[:serve.soc_a000_where_id_byte_len] +\
        serve.soc_a000_dept_passwords_sign_ple_byte +\
        len(serve.a000_ple_password).to_bytes(1, 'big') +\
        serve.a000_ple_password.encode()

        temp_byte = temp_byte +\
        serve.soc_a000_dept_passwords_sign_byte +\
        client_data[:serve.soc_a000_where_id_byte_len] +\
        serve.soc_a000_dept_passwords_sign_me_byte +\
        len(serve.a000_me_password).to_bytes(1, 'big') +\
        serve.a000_me_password.encode()
        client_data = client_data[serve.soc_a000_where_id_byte_len:]

    connection.sendall(temp_byte)
    try:
        while True:
            client_data = connection.recv(1024)
            temp_byte = serve.soc_a000_prod_data_sign_byte + a000_unique_no_in_bytes
            data_avl_flag = False
            for where_id in client_where_id_list:
                if not communication_dict[where_id]["send_data_queue"].empty():
                    temp_byte = temp_byte + communication_dict[where_id]["send_data_queue"].get()
                    data_avl_flag = True
            if client_data == soc_esc_data:
                if not data_avl_flag:
                    time.sleep(0.1)
            else:
                data_spliter_to_apps_queue.put(client_data)
            connection.sendall(temp_byte)
    except:
        for where_id in client_where_id_list:
            communication_dict[where_id]["soc_connection"] = False


def data_spliter_to_clients(app_to_client_queue):
    logged_flag=False
    while True:
        try:
            where_id, send_data = app_to_client_queue.get()
            if communication_dict[where_id]["send_data_queue"].full():
                a000_bw_logger.warning(communication_dict[where_id]["send_data_queue"].get())
            communication_dict[where_id]["send_data_queue"].put(send_data)
            if logged_flag:
                logged_flag=False
        except Exception as e:
            if not logged_flag:
                a000_bw_logger.error("Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(serve.error_wait)


def data_spliter_to_apps():
    logged_flag=False
    while True:
        try:
            raw_data = data_spliter_to_apps_queue.get()
            raw_data = bytearray(raw_data)
            while raw_data:
                sign = raw_data[0]
                data_len = int.from_bytes(raw_data[1:][:serve.soc_a000_data_pack_size_byte_len], 'big')
                start = 1+serve.soc_a000_data_pack_size_byte_len
                end = 1+serve.soc_a000_data_pack_size_byte_len+data_len
                where_id = int.from_bytes(raw_data[start:][:serve.soc_a000_where_id_byte_len], 'big')
                communication_dict[where_id]["data_last_recv_time"] = time.time()
                if (not communication_dict[where_id]["ps_connection"]) and communication_dict[where_id]["ps_connection"] != None :
                    communication_dict[where_id]["ps_connection"] = True
                    maintenance_chat_queue.put(["C", where_id, communication_dict[where_id]["data_last_recv_time"]])
                for client_to_app_queue in client_to_app_queues_dic:
                    if sign in client_to_app_queues_dic[client_to_app_queue]:
                        client_to_app_queue.put(raw_data[0:1] + raw_data[start:end])
                        break
                raw_data = raw_data[end:]
            if logged_flag:
                logged_flag=False
        except Exception as e:
            if not logged_flag:
                a000_bw_logger.error("Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(serve.error_wait)


def send_passwords():
    pass
#     for where_id in communication_dict:
#         communication_dict[where_id]["send_data_queue"].put(send_data)


def accept_connections(ServerSocket):
    conn, address = ServerSocket.accept()
    a000_bw_logger.info(f'Connected to: {address[0]}:{address[1]}')
    serve.run_as_thread(client_handler,args=(conn,))


def start_server():
    logged_flag=False
    while True:
        try:
            ServerSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            try:
                ServerSocket.bind((serve.ipaddress_of_system,serve.xylem_listen_port))
            except socket.error as e:
                if not logged_flag:
                    a000_bw_logger.error(str(e))
                    logged_flag=True
                time.sleep(serve.error_wait)
                continue
            a000_bw_logger.info(f'{serve.an_xylem_master}: SS: Xylem server is listing on the port {serve.xylem_listen_port}...')
            ServerSocket.listen()
            while True:
                accept_connections(ServerSocket)
                if logged_flag:
                    logged_flag=False
        except Exception as e:
            if not logged_flag:
                a000_bw_logger.error("Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(serve.error_wait)


def monitor_clients():
    while True:
        for where_id in communication_dict:
            if communication_dict[where_id]["ps_connection"] or communication_dict[where_id]["ps_connection"]==None :
                if (communication_dict[where_id]["data_last_recv_time"] + communication_dict[where_id]["ma_trig_delay"]) < time.time():
                    communication_dict[where_id]["ps_connection"] = False
                    last_recv_time=datetime.datetime.fromtimestamp(communication_dict[where_id]["data_last_recv_time"])
                    maintenance_chat_queue.put(["O", where_id, last_recv_time])
        time.sleep(1)


def	google_chat_maintenance():
    logged_flag=False
    while True:
        try:
            type_c, where_id, last_recv_time = maintenance_chat_queue.get()
            ps = serve.get_icode_object(where_id)
            pl = serve.get_production_line_of_ps(production_station_id = where_id)
            if type_c=="O":
                chat_data = f'<i><b><u>{serve.an_xylem_master}: No values received Intimation!</u></b></i>\n'\
                            f'No value received from the <b><u>{pl.name}: {ps.name}</u></b> since <b><u>{last_recv_time}</u></b>'
            elif type_c=="C":
                chat_data = f'<font color=\"#00ff00\"><i><b><u>{serve.an_xylem_master}: Values received Intimation!</u></b></i>\n'\
                            f'Value received from the </font><b><u>{pl.name}: {ps.name}</u></b><font color=\"#00ff00\"> on <b><u>{last_recv_time}</u></b></font>'
            retry_count = 0
            while retry_count <= serve.chat_max_retry_count:
                try:
                    data_dir = {"cards": [{"sections":[{"widgets":[{"textParagraph":{ 'text':f'{chat_data}'}}]}]}]}#,
                    r = requests.post(serve.a000_soc_maintenance_space_url, data=json.dumps(data_dir))
                    a000_bw_logger.info(f'{serve.an_xylem_master}: GCM: Google chat maintence message sent ({type_c})...{time.strftime("%d-%m-%Y_%I.%M.%S_%p")} {pl.name}: {ps.name}')
                except Exception as e:
                    a000_bw_logger.warning(f"{serve.an_xylem_master}: GCM: Connection Error! check internet connection. Retrying to connect... \n Error: {e}")
                    time.sleep(3)
                    retry_count = retry_count+1
                    continue
                break
            if logged_flag:
                logged_flag=False
        except Exception as e:
            if not logged_flag:
                a000_bw_logger.error("Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(serve.error_wait)

serve.run_as_thread(data_spliter_to_apps)
for app_to_client_queue in app_to_client_queues_dic:
    serve.run_as_thread(data_spliter_to_clients, args=(app_to_client_queue,))

try:
    for SocketWhereID in SocketWhereIDs.objects.select_related("where_id"):
        where_id = SocketWhereID.where_id.icode
        communication_dict[where_id] = sub_dict_default.copy()
        communication_dict[where_id]["send_data_queue"] = queue.Queue(maxsize=30)
        communication_dict[where_id]["ma_trig_delay"] = SocketWhereID.ma_trig_delay
        communication_dict[where_id]["data_last_recv_time"] = time.time()
except (ProgrammingError, SocketWhereIDs.DoesNotExist) as e :
    a000_bw_logger.error("Exception occurred", exc_info=True)

update_a000_unique_no()


if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
	# serve.run_as_thread(start_server)
    # serve.run_as_thread(monitor_clients)
    # serve.run_as_thread(google_chat_maintenance)
    # schedule.every().day.at("00:00:00").do(update_a000_unique_no,)
	pass

elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
    serve.run_as_thread(start_server)
    serve.run_as_thread(monitor_clients)
    serve.run_as_thread(google_chat_maintenance)
    schedule.every().day.at("00:00:00").do(update_a000_unique_no,)

elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
    serve.run_as_thread(start_server)
    serve.run_as_thread(monitor_clients)
    serve.run_as_thread(google_chat_maintenance)
    schedule.every().day.at("00:00:00").do(update_a000_unique_no,)