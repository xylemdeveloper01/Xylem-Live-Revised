import math, time, datetime, schedule, logging
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q, Sum, Max
from django.db.models.functions import Coalesce

from xylem.settings import EMAIL_HOST_USER, XYLEM_MODE, XYLEM_MODE_DIC
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import TPsMapping
from xylem_apps.a000_xylem_master.background_works.main_socket import a004_app_to_client_queue
from xylem_apps.a004_tools_management_system.models import ToolHistoryLog, ToolAlert
from xylem_apps.a004_tools_management_system.tms_serve import get_tps_maps_with_low_life_by_pc
from xylem_apps.a007_oee_monitoring.models import ProductionChangeOvers
from xylem_apps.a007_oee_monitoring.background_works.oee_handler import oee_dict


a004_bw_logger = logging.getLogger(serve.Apps.A004ToolsManagementSystem.bw_logger_name)
a004_production_interruption_dict = {}
current_send_alert_th = None


def production_line_interlock_handler():
    global a004_production_interruption_dict
    while True:
        temp_life_over_interrupt_dic = {}
        for pc in serve.get_product_categories():
            for i in get_tps_maps_with_low_life_by_pc(product_category=pc):
                if i["avl_tool_life"] <= 5:
                    pl = serve.get_production_line_of_ps(production_station_id=i["tps_map"].production_station_i_id)
                    msg = "\n".join(["TMS Alert (A004): Tool life over!", "Tool: "+i["tps_map"].tool_i.name, "Location: "+pl.name+i["tps_map"].production_station_i.name])
                    if not pl.icode in temp_life_over_interrupt_dic:
                        temp_life_over_interrupt_dic[pl.icode] = msg
                    else:
                        temp_life_over_interrupt_dic[pl.icode] = temp_life_over_interrupt_dic[pl.icode]+'\n\n'+ msg
        a004_production_interruption_dict = temp_life_over_interrupt_dic
        time.sleep(1)


def data_encode():
    a004_production_interrupted_list = []
    while True:
        temp_dic = a004_production_interruption_dict.copy()
        for where_id_pl in oee_dict:
            where_id_ps = oee_dict[where_id_pl]["where_id_ps"]
            temp_byte = b''
            if where_id_pl in temp_dic:
                a004_production_interrupt_msg_byte = temp_dic[where_id_pl][:serve.max_byte_len_of_production_interrupt_msg].encode()
                temp_byte = temp_byte + serve.soc_a000_production_interrupt_sign_byte +\
                    where_id_ps.to_bytes(serve.soc_a000_where_id_byte_len, 'big') +\
                    serve.soc_a000_production_interrupt_sign_up_byte  +\
                    len(a004_production_interrupt_msg_byte).to_bytes(1, 'big') + a004_production_interrupt_msg_byte
                if not where_id_pl in a004_production_interrupted_list:
                    a004_production_interrupted_list.append(where_id_pl)
            elif where_id_pl in a004_production_interrupted_list:
                temp_byte = temp_byte + serve.soc_a000_production_interrupt_sign_byte +\
                    where_id_ps.to_bytes(serve.soc_a000_where_id_byte_len, 'big') +\
                    serve.soc_a000_production_interrupt_sign_down_byte
                a004_production_interrupted_list.remove(where_id_pl)
            if temp_byte:
                a004_app_to_client_queue.put([where_id_ps,temp_byte])
        time.sleep(1)


def send_alerts():
    try:
        today_date = datetime.datetime.now().date()
        alert_tps_map_list = []
        for pc in serve.get_product_categories():
            tps_map_list = get_tps_maps_with_low_life_by_pc(product_category=pc)
            for i in tps_map_list:
                tool_alert = ToolAlert.objects.filter(tps_map=i["tps_map"], alert_date=today_date)
                if tool_alert.exists():
                    continue
                alert_tps_map_list.append(i)
        if alert_tps_map_list:
            no_of_tools = len(alert_tps_map_list)
            subject = f"X-A004 Alert : Low Tool Life"
            to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a004_low_tool_life_alert_mail)
            if no_of_tools>1:
                subject = subject + f" ({no_of_tools} Tools)"
            html_content = render_to_string('a004/tms_alert_mail.html', {'alert_tps_map_list': alert_tps_map_list})
            serve.send_mail(app_name = serve.an_tools_management_system, subject = subject, to_list = to_list, html_content = html_content)
            for i in alert_tps_map_list:
                ToolAlert.objects.update_or_create(
                    tps_map=i["tps_map"],
                    defaults={"alert_date": today_date}
                )
    except Exception as e:
        a004_bw_logger.error("Exception occurred", exc_info=True)
        time.sleep(serve.error_wait)


if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
    pass

elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
    pass

elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
    serve.run_as_thread(production_line_interlock_handler)
    serve.run_as_thread(data_encode)
    schedule.every().minute.do(serve.run_as_thread, send_alerts,)