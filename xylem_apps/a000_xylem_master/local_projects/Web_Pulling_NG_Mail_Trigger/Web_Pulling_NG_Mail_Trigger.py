import os, sys, time, json, threading, logging
from django.core.mail import EmailMultiAlternatives

from xylem.settings import EMAIL_HOST_USER

from xylem_apps.a000_xylem_master import serve

a000_bw_logger = logging.getLogger(serve.Apps.A000XylemMaster.bw_logger_name)


json_file_name = "NG_data.json"
partno_model_dic = {
    "": "M&M FRONT PT+DLT+APT Z101 9MM",
    "021 0007 00": "M&M FRONT PT+DLT+APT Z101 9MM",
    "021 0008 00": "M&M FRONT PT+DLT+APT Z101 9MM",
    "alert_test": "testing alert, pls ignore",
}
app_folder_path = ".\\xylem_apps\\a000_xylem_master\\local_projects\\Web_Pulling_NG_Mail_Trigger\\"

def web_pulling_ng_mail_trigger():
    json_file = os.path.join(app_folder_path, json_file_name).replace('\\', '\\\\')
    while True:             
        if os.path.isfile(json_file):
            a000_bw_logger.info(f"Local Project - Web Pulling NG Alert Mail: NG trigger file identified, path: {json_file}")
            json_read_file = open(json_file,"r")
            loaded_str = json_read_file.read()
            json_read_file.close()
            loaded_dict = json.loads(loaded_str)
            line_name = loaded_dict['Line']
            serial_no = loaded_dict['Barcode']
            part_no = loaded_dict['Partno']
            part_description = partno_model_dic[part_no]
            dt = loaded_dict['dt']
            html_str = f'''
                <!DOCTYPE html>
                <html>
                <body>

                <h1 style="text-align: center;">Web Pulling NG Part Data</h1>

                <table align="center" style="font-family: Arial, Helvetica, sans-serif;
                border-collapse: collapse; ">
                <tr>
                <th style="border: 1px solid #ddd;padding: 8px; padding-top: 12px;
                padding-bottom: 12px;
                text-align: left;
                background-color: #F70D1A;
                color: white;">Production line</th>
                <td style="border: 1px solid #ddd;padding: 8px;background-color: #f2f2f2;">{line_name}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd;padding: 8px; padding-top: 12px;
                    padding-bottom: 12px;
                    text-align: left;
                    background-color: #F70D1A;
                    color: white;">Barcode data</th>
                    <td style="border: 1px solid #ddd;padding: 8px;background-color: #f2f2f2;">{serial_no}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd;padding: 8px; padding-top: 12px;
                    padding-bottom: 12px;
                    text-align: left;
                    background-color: #F70D1A;
                    color: white;">Part No</th>
                    <td style="border: 1px solid #ddd;padding: 8px;background-color: #f2f2f2;">{part_no}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd;padding: 8px; padding-top: 12px;
                    padding-bottom: 12px;
                    text-align: left;
                    background-color: #F70D1A;
                    color: white;">Part Description</th>
                    <td style="border: 1px solid #ddd;padding: 8px;background-color: #f2f2f2;">{part_description}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd;padding: 8px; padding-top: 12px;
                    padding-bottom: 12px;
                    text-align: left;
                    background-color: #F70D1A;
                    color: white;">Time of Running</th>
                    <td style="border: 1px solid #ddd;padding: 8px;background-color: #f2f2f2;">{dt}</td>
                </tr>
                </table>
                {serve.get_xylem_manage_mail_footer_html()}
                </body>
                </html>
            '''
            subject = "Alert: Web Pulling NG"
            to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a000_local_projects_alert_web_pulling_ng_mail)
            serve.send_mail(app_name = "Local Project - Web Pulling NG Alert Mail", subject = subject, to_list = to_list, html_content = html_str)
            os.remove(json_file)
        else:
            time.sleep(1)


threading.Thread(target = web_pulling_ng_mail_trigger, daemon = True).start()
