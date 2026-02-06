import os, sys, time, datetime, json, threading, logging
from django.template.loader import render_to_string

from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import Icodes
from xylem_apps.a003_smart_alerts.models import FrictionWeldingAlerts, FrictionWeldingLastReadData


a003_bw_logger = logging.getLogger(serve.Apps.A003SmartAlerts.bw_logger_name)

stn_log_folder_path = r"\\10.173.1.19\resultdata\LOG\Overall"


def friction_welding_ng_mail_trigger():
    logged_flag = False
    while True:
        try:
            time.sleep(1)
            current_dt = datetime.datetime.now()
            last_data_object, created = FrictionWeldingLastReadData.objects.get_or_create(where_id_i=serve.Others.where_id_obj_spr8_bb_friction_welding_machine, defaults = {'last_checked_logged_dt': current_dt, "last_checked_modified_dt": current_dt})
            lookup_files_list = []
            max_last_modified_dt = last_data_object.last_checked_modified_dt
            for filename in os.listdir(stn_log_folder_path):
                file_path = os.path.join(stn_log_folder_path, filename)
                if os.path.isfile(file_path):
                    last_modified_dt = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    if last_modified_dt > last_data_object.last_checked_modified_dt:
                        lookup_files_list.append(file_path)
                    if max_last_modified_dt < last_modified_dt:
                        max_last_modified_dt = last_modified_dt
            max_logged_dt = last_data_object.last_checked_logged_dt
            if lookup_files_list:
                ng_log_data_list = []
                for file_path in lookup_files_list:
                    with open(file_path, "r", encoding="utf-8") as file:
                        file_lines = file.readlines()
                        file_head_data_1 = file_lines[0].strip().split(";")
                        file_head_data_2 = file_lines[1].strip().split(";")
                        file_head_data_3 = file_lines[2].strip().split(";")

                        # strip each element inside the lists
                        file_head_data_1 = [x.strip() for x in file_head_data_1]
                        file_head_data_2 = [x.strip() for x in file_head_data_2]
                        file_head_data_3 = [x.strip() for x in file_head_data_3]

                        # combine same-index elements with space
                        file_head_data_combined = [
                            f"{a} {b} {c}".lower()
                            for a, b, c in zip(file_head_data_1, file_head_data_2, file_head_data_3)
                        ]

                        file_lines_wo_head = file_lines[3:] 
                        logged_dt_col_index = file_head_data_combined.index("m032 - zf ind 1 overall station 6 date/time")
                        part_desc_col_index = file_head_data_combined.index("general overall typename")
                        part_barcode_col_index = file_head_data_combined.index("general overall dmc retractor")
                        mgg_barcode_col_index = file_head_data_combined.index("general overall dmc mgg")
                        overall_status_col_index = file_head_data_combined.index("general overall overall - ok status")
                        fwm_status_col_index = file_head_data_combined.index("st04 fwm ok status")
                        angle_status_col_index = file_head_data_combined.index("st05 cam angle ok status")
                        for file_line in reversed(file_lines_wo_head):
                            file_line = file_line.strip()
                            if file_line:
                                file_line_data = file_line.split(";")
                                file_line_data = [x.strip() for x in file_line_data]
                                logged_dt = datetime.datetime.strptime(file_line_data[logged_dt_col_index], "%m/%d/%Y %I:%M:%S %p")
                                if logged_dt > last_data_object.last_checked_logged_dt:
                                    overall_status = file_line_data[overall_status_col_index].strip().lower() == "true"
                                    if not overall_status:
                                        fwm_status = file_line_data[fwm_status_col_index].strip().lower() == "true"
                                        angle_status = file_line_data[angle_status_col_index].strip().lower() == "true"
                                        if (not fwm_status) or (not angle_status):
                                            ng_log_data_list.append({
                                                "logged_dt": logged_dt,
                                                "part_desc": file_line_data[part_desc_col_index],
                                                "part_barcode": file_line_data[part_barcode_col_index],
                                                "mgg_barcode": file_line_data[mgg_barcode_col_index],
                                                "overall_status": overall_status,
                                                "fwm_status": fwm_status,
                                                "angle_status": angle_status,
                                            })
                                    if max_logged_dt < logged_dt:
                                        max_logged_dt = logged_dt
                                else:
                                    break
                if ng_log_data_list:
                    friction_welding_ng_obj_list = []
                    for ng_log_data in ng_log_data_list:
                        friction_welding_ng_obj = FrictionWeldingAlerts.objects.create(
                            where_id_i = serve.Others.where_id_obj_spr8_bb_friction_welding_machine,
                            part_barcode_data = ng_log_data["part_barcode"],
                            mgg_barcode_data = ng_log_data["mgg_barcode"],
                            part_description = ng_log_data["part_desc"],
                            ng_description = "Friction Welding Not Ok" if not ng_log_data["fwm_status"] else "Friction Welding Angle Not Ok",
                            logged_dt = ng_log_data["logged_dt"],
                        )
                        friction_welding_ng_obj_list.append(friction_welding_ng_obj)
                    no_of_ng = len(friction_welding_ng_obj_list)
                    subject = f"X-A003 Alert: Friction Welding NG Alert (Trial)"
                    to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a003_friction_welding_ng_alert_mail)
                    if no_of_ng>1:
                        subject = subject + f" ({no_of_ng} NGs)"
                    html_content = render_to_string('a003/friction_welding_alert_mail.html', {'friction_welding_ng_obj_list': friction_welding_ng_obj_list})
                    serve.send_mail(app_name = serve.an_smart_alerts, subject = subject, to_list = to_list, html_content = html_content)
                    
                last_data_object.last_checked_logged_dt = max_logged_dt
                last_data_object.last_checked_modified_dt = max_last_modified_dt
                last_data_object.save()
            if logged_flag:
                logged_flag = False
        except Exception as e:
            if not logged_flag:
                a003_bw_logger.error("Exception occurred", exc_info=True)
                logged_flag = True
            time.sleep(serve.error_wait)

threading.Thread(target=friction_welding_ng_mail_trigger, daemon=True).start()

# USE [a000_xylem_master]
# GO

# INSERT INTO [dbo].[a000_xylem_master_icodes]
#       ([icode]
#       ,[name]
#       ,[description]
#       ,[last_edited])
      
# VALUES

# (413, '', NULL, CURRENT_TIMESTAMP),
# (414, 'X-A003 Alert: Friction Welding NG Alert (Trial)', NULL, CURRENT_TIMESTAMP)

# USE [a000_xylem_master]
# GO

# INSERT INTO [dbo].[a000_xylem_master_maildepartmentmapping]
#       ([dept_id]
#       ,[mail_i_id])
# VALUES
#       (121,	413),
#       (122,	413),
#       (123,	413),
#       (124,	413),
#       (131,	413),
#       (134,	413),
#       (126,	413)
# GO

