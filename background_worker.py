import os, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xylem.settings")
django.setup()


import django, datetime, random
from flask import Flask, jsonify, request

from xylem.settings import XYLEM_MODE, XYLEM_MODE_DIC


folder_name_of_restart_files = "xylem_bw_restart_history"
if not os.path.exists(folder_name_of_restart_files):
	os.mkdir(folder_name_of_restart_files)
temp = os.path.join(folder_name_of_restart_files, datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f') + f"_{random.randint(1,100000)}.txt")
f = open(temp, "w")
f.write(f"i have restarted {temp}")
f.close()
from xylem_apps.a000_xylem_master import serve

from xylem_apps.a000_xylem_master.background_works import main_socket, scheduler, unsentmail_handler, xr_handler, xr_websocket
from xylem_apps.a001_qa_report_and_reprocess.background_works import main_server
from xylem_apps.a002_sbs_rejection_entry_and_rework.background_works import *
from xylem_apps.a003_smart_alerts.background_works import web_pulling_ng_alerts
from xylem_apps.a004_tools_management_system.background_works import tms_handler
from xylem_apps.a005_qa_patrol_check.background_works import *
from xylem_apps.a006_4m_digitalization.background_works import xr_handler, form_handler
from xylem_apps.a007_oee_monitoring.background_works import oee_handler
from xylem_apps.a008_home_schemer.background_works import *
from xylem_apps.a009_building_management_system.background_works import bms_handler
from xylem_apps.a010_poka_yoke_monitoring.background_works import pms_handler


if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
    from xylem_apps.a003_smart_alerts.background_works import friction_welding_ng_mail_trigger
    pass

elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
    pass

elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
    from xylem_apps.a000_xylem_master.local_projects.IFS1_Vision_Server import IFS1_Vision_Server
    from xylem_apps.a003_smart_alerts.background_works import cop_alerts, web_pulling_ng_alerts, friction_welding_ng_mail_trigger


app = Flask(__name__)


@app.route('/')
def home():
    return "XYLEM BACKGROUND WORKER"


@app.route(serve.a001_mainserver_connect_url + '/<int:work_type>/<int:line_id>/<int:stn_id>')
def a001_mainserver_connect(work_type, line_id, stn_id):
    return jsonify(main_server.mainserver_connect(work_type, line_id, stn_id))


@app.post(serve.a001_mainserver_get_data_url)
def a001_mainserver_get_data():
    data = request.get_json()
    return main_server.mainserver_get_data(data["connection_id"], data.get("serialNo"), data.get("fromDate"), data.get("toDate"))


@app.post(serve.a001_mainserver_update_data_url)
def a001_mainserver_update_data():
    data = request.get_json()
    return jsonify(main_server.mainserver_update_data(data["connection_id"], data["serialNo"], data["remarks"]))


@app.route(serve.a006_get_four_m_mail_url + '/<int:four_m_id>')
def a006_get_four_m_mail(four_m_id):
    serve.run_as_thread(form_handler.send_four_m_mail, args = (four_m_id,))
    return {"status": 100}


@app.route(serve.a007_get_dashboard_dict_url + '/<int:line_id>')
def a007_get_dashboard_dict(line_id):
    return oee_handler.get_dashboard_dict(line_id)


@app.post(serve.a007_get_dashboard_report_dict_url)
def a007_get_dashboard_report_dict():
    data = request.get_json()
    production_line_ids = data.get("production_line_ids")
    date = data.get("date")
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    shift_id = data.get('shift_id')
    shift = serve.get_shift_obj(shift_id=shift_id)
    return oee_handler.get_dashboard_report_dict(production_line_ids, date, shift)


@app.route(serve.a009_get_pc_dashboard_dict_url)
def a009_get_pc_dashboard_dict():
    return bms_handler.get_pc_dashboard_dict()


@app.route(serve.a009_get_wc_dashboard_dict_url)
def a009_get_wc_dashboard_dict():
    return bms_handler.get_wc_dashboard_dict()


@app.route(serve.a010_get_poka_yoke_tree_dict_of_pc_url + '/<int:product_category_id>')
def a010_get_poka_yoke_tree_dict_of_pc(product_category_id):
    return pms_handler.get_poka_yoke_tree_dict_of_pc(product_category_id)


@app.route(serve.a010_get_poka_yoke_fruit_clusters_dict_url + '/<int:production_line_id>')
def a010_get_poka_yoke_fruit_clusters_dict(production_line_id):
    return pms_handler.get_poka_yoke_fruit_clusters_dict(production_line_id)


@app.route(serve.a010_get_poka_yoke_fruits_dict_url + '/<int:production_station_id>')
def a010_get_poka_yoke_fruits_dict(production_station_id):
    return pms_handler.get_poka_yoke_fruits_dict(production_station_id)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='127.0.0.1', port=5002)    