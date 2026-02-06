import math, time, datetime, schedule, logging
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q, F, Sum, Max
from django.db.models.functions import Cast, Coalesce, TruncDate

from xylem.settings import EMAIL_HOST_USER, XYLEM_MODE, XYLEM_MODE_DIC
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import PyPsMapping
from xylem_apps.a010_poka_yoke_monitoring.models import PokaYokeInspections
from xylem_apps.a010_poka_yoke_monitoring.pms_serve import get_pyps_maps_of_awaiting_inspections


# pls - production lines, pl_id - production line id, ps_id - production station id, ft: fruit type, nf: no of fruits,
# h_ok_f - harvested ok fruits, h_nok_f - harvested nok fruits, h_missed_f - harvested missed fruits, py_list - pokayoke list
# below are the sample formats of dict
# poka_yoke_tree_dict = {
#     "pls": {
#         "pl_id": [
#             {
#                 "ft" : 0,
#                 "nf" : 0
#             },
#         ],
#     },
#     "h_ok_f": 0,
#     "h_nok_f": 0,
#     "h_missed_f": 0,
# }
# poka_yoke_fruit_clusters_dict = {
#     "pl_id": {
#         "ps_id": [
#             {
#                 "ft" : 0,
#                 "nf" : 0
#             },
#         ],
#     }
# }
# poka_yoke_fruits_dict = {
#     "pl_id": {
#         "ps_id":{
#             "py_id": {
#                 "ft" : 0,
#             }
#         }
#     }
# }

a010_bw_logger = logging.getLogger(serve.Apps.A010PokaYokeMonitoring.bw_logger_name)

          
poka_yoke_tree_dict = {}
poka_yoke_fruit_clusters_dict = {}
poka_yoke_fruits_dict = {}
current_dt = None

inspec_ok = serve.Apps.A010PokaYokeMonitoring.inspec_ok
inspec_nok = serve.Apps.A010PokaYokeMonitoring.inspec_nok
inspec_waiting = serve.Apps.A010PokaYokeMonitoring.inspec_waiting
inspec_missed = serve.Apps.A010PokaYokeMonitoring.inspec_missed


def close_over_due_inspections(send_mail = None):
    for index_pc, pc in enumerate(serve.get_product_categories()):
        pyps_inspections_await = get_pyps_maps_of_awaiting_inspections(product_category=pc) if not index_pc\
            else pyps_inspections_await.union(get_pyps_maps_of_awaiting_inspections(product_category=pc))
    today_date = datetime.datetime.now().date()
    while True:
        temp_list = []
        for pyps_map in  pyps_inspections_await:
            if pyps_map.upcoming_due_date<today_date:
                temp_list.append(
                    PokaYokeInspections(
                        pyps_map = pyps_map,
                        inspection_due_date = pyps_map.upcoming_due_date,
                    )
                )
        if not temp_list:
            break
        PokaYokeInspections.objects.bulk_create(temp_list)
        time.sleep(.1)

    if send_mail:
        serve.run_as_thread(send_pokeyoke_mail)


def update_poka_yoke_tree_dict():
    global current_dt
    while True:
        current_dt = datetime.datetime.now()
        pc_id_list = list(serve.get_product_categories().values_list("icode", flat=True))
        pyps_inspec_harvest_m = PokaYokeInspections.objects.filter(inspection_datetime__month = current_dt.month, inspection_datetime__year = current_dt.year, inspection_due_date__lt = current_dt.date())
        pyps_inspec_harvest_m_ok = pyps_inspec_harvest_m.filter(inspection_status = inspec_ok)
        pyps_inspec_harvest_m_nok = pyps_inspec_harvest_m.filter(inspection_status = inspec_nok)
        pyps_inspec_harvest_m_missed = pyps_inspec_harvest_m.filter(inspection_status = inspec_missed)
        poka_yoke_tree_dict["h_ok_f"] = pyps_inspec_harvest_m_ok.count()
        poka_yoke_tree_dict["h_nok_f"] = pyps_inspec_harvest_m_nok.count()
        poka_yoke_tree_dict["h_missed_f"] = pyps_inspec_harvest_m_missed.count()
        pyps_inspec_awaiting_harvest_m = PokaYokeInspections.objects.filter(inspection_datetime__month = current_dt.month, inspection_datetime__year = current_dt.year, inspection_due_date__gte = current_dt.date()).values_list("pyps_map", "inspection_status")
        pyps_curr_status_dict = {}
        pls_dict = {}
        pls_pss_dict = {}
        for pyps_map_id, inspec_status in pyps_inspec_awaiting_harvest_m:
            pyps_curr_status_dict[pyps_map_id]= inspec_status
        for pc_id in pc_id_list:
            for pyps_map_id in serve.get_pyps_maps_of_pc(product_category_id = pc_id).values_list("id", flat=True):
                if not pyps_map_id in pyps_curr_status_dict:
                    pyps_curr_status_dict[pyps_map_id] = None
            for pl in serve.get_production_lines(product_category_id=pc_id):
                pss = serve.get_production_stations(production_line=pl)
                temp_list = list(PyPsMapping.objects.filter(production_station_i__in = pss ).values_list("id", flat=True))
                if not temp_list:
                    continue
                pls_dict[pl.icode] = temp_list
                pls_pss_dict[pl.icode] = {}
                for ps in pss:
                    temp_list = list(PyPsMapping.objects.filter(production_station_i = ps ).values_list("id", flat=True))
                    if temp_list:
                        pls_pss_dict[pl.icode][ps.icode] = temp_list

        poka_yoke_tree_dict["pls"] = {}
        for pl_id in pls_dict:
            temp_list = []
            for pyps_map_id in pls_dict[pl_id]:
                temp_list.append(pyps_curr_status_dict[pyps_map_id])
            if temp_list:
                ok_f, nok_f, waiting_f = temp_list.count(inspec_ok), temp_list.count(inspec_nok), temp_list.count(inspec_waiting)
                temp_list = []
                if ok_f : temp_list.append({"ft":inspec_ok, "nf":ok_f}) 
                if nok_f : temp_list.append({"ft":inspec_nok, "nf":nok_f}) 
                if waiting_f : temp_list.append({"ft":inspec_waiting, "nf":waiting_f}) 
                poka_yoke_tree_dict["pls"][pl_id] = sorted(temp_list, key=lambda x:x["nf"], reverse=True)
            
            poka_yoke_fruit_clusters_dict[pl_id] = {}
            poka_yoke_fruits_dict[pl_id] = {}
            for ps_id in pls_pss_dict[pl_id]:
                temp_list = []
                poka_yoke_fruits_dict[pl_id][ps_id]={}
                pyps_map_id_py_id_list = list(PyPsMapping.objects.filter(id__in = pls_pss_dict[pl_id][ps_id]).values_list("id","poka_yoke_i"))
                for pyps_map_id, py_id in pyps_map_id_py_id_list:
                    poka_yoke_fruits_dict[pl_id][ps_id][py_id] = {"ft":pyps_curr_status_dict[pyps_map_id]}
                for pyps_map_id in pls_pss_dict[pl_id][ps_id]:
                    temp_list.append(pyps_curr_status_dict[pyps_map_id])
                if temp_list:
                    ok_f , nok_f, waiting_f = temp_list.count(inspec_ok), temp_list.count(inspec_nok), temp_list.count(inspec_waiting)
                    temp_list = []
                    if ok_f : temp_list.append({"ft":inspec_ok, "nf":ok_f}) 
                    if nok_f : temp_list.append({"ft":inspec_nok, "nf":nok_f}) 
                    if waiting_f : temp_list.append({"ft":inspec_waiting, "nf":waiting_f}) 
                    poka_yoke_fruit_clusters_dict[pl_id][ps_id] = sorted(temp_list, key=lambda x:x["nf"], reverse=True)
        # print("===========> ", poka_yoke_tree_dict)
        # print("===========> ", poka_yoke_fruit_clusters_dict)
        # print("===========> ", pyps_curr_status_dict)
        # print("===========> ", poka_yoke_fruits_dict)
        time.sleep(1)
        

def get_poka_yoke_tree_dict_of_pc(product_category_id):
    product_category_id = int(product_category_id)
    poka_yoke_tree_pc_dict = {}
    poka_yoke_tree_pls_dict = poka_yoke_tree_dict["pls"]
    pls = serve.get_production_lines(product_category_id=product_category_id).values_list('icode', flat=True)
    for pl in pls:
        if pl in poka_yoke_tree_pls_dict:
            poka_yoke_tree_pc_dict[pl] = poka_yoke_tree_pls_dict[pl]
    # print(poka_yoke_tree_pc_dict)
    return poka_yoke_tree_pc_dict


def get_poka_yoke_fruit_clusters_dict(production_line_id):
    return poka_yoke_fruit_clusters_dict[production_line_id]


def get_poka_yoke_fruits_dict(production_station_id):
    pl_id = serve.get_production_line_of_ps(production_station_id=production_station_id).icode
    return poka_yoke_fruits_dict[pl_id][production_station_id]


def send_pokeyoke_mail():
    to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a010_poke_yoke_status_update_mail)
    subject = f"X-A010 : Poka Yoke Status Update {current_dt.date()}"
    temp_list = []
    for pl_id in poka_yoke_tree_dict["pls"]:
        for pl_ft_data_dict in poka_yoke_tree_dict["pls"][pl_id]:
            if pl_ft_data_dict["ft"] == inspec_ok:
                temp_list.append(pl_ft_data_dict["nf"])
    ok_f = sum(temp_list)
    temp_list = []
    for pl_id in poka_yoke_tree_dict["pls"]:
        for pl_ft_data_dict in poka_yoke_tree_dict["pls"][pl_id]:
            if pl_ft_data_dict["ft"] == inspec_nok:
                temp_list.append(pl_ft_data_dict["nf"])
    nok_f = sum(temp_list)
    temp_list = []
    for pl_id in poka_yoke_tree_dict["pls"]:
        for pl_ft_data_dict in poka_yoke_tree_dict["pls"][pl_id]:
            if pl_ft_data_dict["ft"] == inspec_waiting:
                temp_list.append(pl_ft_data_dict["nf"])
    waiting_f = sum(temp_list)

    tf_in_tree = ok_f + nok_f + waiting_f
    ok_f_p = serve.convert_float_with_int_possibility((ok_f/tf_in_tree)*100, 2)
    nok_f_p = serve.convert_float_with_int_possibility((nok_f/tf_in_tree)*100, 2)
    waiting_f_p = serve.convert_float_with_int_possibility((waiting_f/tf_in_tree)*100, 2)
    
    thf = poka_yoke_tree_dict["h_ok_f"] + poka_yoke_tree_dict["h_nok_f"] + poka_yoke_tree_dict["h_missed_f"]
    h_ok_p = serve.convert_float_with_int_possibility((poka_yoke_tree_dict["h_ok_f"]/thf)*100, 2)
    h_nok_p = serve.convert_float_with_int_possibility((poka_yoke_tree_dict["h_nok_f"]/thf)*100, 2)
    h_missed_p = serve.convert_float_with_int_possibility((poka_yoke_tree_dict["h_missed_f"]/thf)*100, 2)
    
    html_content = render_to_string('a010/poka_yoke_fruit_harvest_mail.html', {
        'today_date': current_dt.date(),
        'thf': thf,
        'ok_f': ok_f,
        'nok_f': nok_f,
        'waiting_f': waiting_f,
        'ok_f_p': ok_f_p,
        'nok_f_p': nok_f_p,
        'waiting_f_p': waiting_f_p,
        'tf_in_tree': tf_in_tree,
        'h_ok_f': poka_yoke_tree_dict["h_ok_f"],
        'h_nok_f': poka_yoke_tree_dict["h_nok_f"],
        'h_missed_f': poka_yoke_tree_dict["h_missed_f"],
        'h_ok_p': h_ok_p,
        'h_nok_p': h_nok_p,
        'h_missed_p': h_missed_p,
    })
    serve.send_mail(app_name = serve.an_poka_yoke_monitoring, subject = subject, to_list = to_list, html_content = html_content)


if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
	serve.run_as_thread(update_poka_yoke_tree_dict)
    # serve.run_as_thread(close_over_due_inspections)
    # schedule.every().day.at("00:00:00").do(serve.run_as_thread,close_over_due_inspections,args=(True,))
	

elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
    serve.run_as_thread(update_poka_yoke_tree_dict)
    serve.run_as_thread(close_over_due_inspections)
    schedule.every().day.at("00:00:00").do(serve.run_as_thread,close_over_due_inspections,args=(True,))

elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
    serve.run_as_thread(update_poka_yoke_tree_dict)
    serve.run_as_thread(close_over_due_inspections)
    schedule.every().day.at("00:00:00").do(serve.run_as_thread,close_over_due_inspections,args=(True,))