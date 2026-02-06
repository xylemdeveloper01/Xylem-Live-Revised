import os, sys, time, json, threading, logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from xylem.settings import EMAIL_HOST_USER

from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import Icodes
from xylem_apps.a003_smart_alerts.models import WebPulligNGAlerts

a003_bw_logger = logging.getLogger(serve.Apps.A003SmartAlerts.bw_logger_name)

json_file_name = "NG_data.json"
partno_model_dic = {
    "": "M&M FRONT PT+DLT+APT Z101 9MM",
    "021 0007 00": "M&M FRONT PT+DLT+APT Z101 9MM",
    "021 0008 00": "M&M FRONT PT+DLT+APT Z101 9MM",
    "alert_test": "testing alert, pls ignore",
}
app_folder_path = ".\\xylem_apps\\a003_smart_alerts\\background_works\\Web_Pulling_NG_Mail_Trigger\\"

def web_pulling_ng_mail_trigger():
    json_file = os.path.join(app_folder_path, json_file_name).replace('\\', '\\\\')
    while True:
        try:
            if os.path.isfile(json_file):
                a003_bw_logger.info(f"Local Project - Web Pulling NG Alert Mail: NG trigger file identified, path: {json_file}")
                with open(json_file, "r") as json_read_file:
                    loaded_dict = json.load(json_read_file)
                pl_icode = loaded_dict.get('Line')
                barcode_data = loaded_dict.get('Barcode')
                part_no = loaded_dict.get('Partno')
                part_description = partno_model_dic.get(part_no)
                dt = loaded_dict.get('dt')
                production_line_i = Icodes.objects.get(icode=int(pl_icode))
                pn_obj = Icodes.objects.filter(name=part_no).first()
                if pn_obj is None:
                    temp_pn = part_no
                    pn = None
                else:
                    temp_pn = None
                    pn = pn_obj
                web_pulg_ng_obj = WebPulligNGAlerts.objects.create(
                    production_line_i=production_line_i,
                    part_number_i=pn,
                    temp_pn=temp_pn,
                    part_description=part_description,
                    barcode_data=barcode_data
                )
                html_content = render_to_string(
                    'a003/web_pulling_ng_mail.html',
                    {'web_pulg_ng_obj': web_pulg_ng_obj}
                )
                subject = "Alert: Web Pulling NG"
                to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a003_web_pulling_ng_alert_mail)
                serve.send_mail(
                    app_name=serve.an_smart_alerts,
                    subject=subject,
                    to_list=to_list,
                    html_content=html_content
                )
                os.remove(json_file)
            else:
                time.sleep(1)
        except json.JSONDecodeError as e:
            a003_bw_logger.error(f"JSON decode error in Web Pulling NG trigger: {e}", exc_info=True)
            time.sleep(2)       
        except Exception as e:
            a003_bw_logger.error(f"Unexpected error in Web Pulling NG mail trigger: {e}", exc_info=True)
            time.sleep(2)


threading.Thread(target = web_pulling_ng_mail_trigger, daemon = True).start()