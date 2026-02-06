import json, socket, time, datetime,logging
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a003_smart_alerts.models import CopPartnumber
from xylem_apps.a007_oee_monitoring.models import ProductionChangeOvers
from django.db.models import Q, F, Sum, When, Case, Value, Avg, Max
from django.template.loader import render_to_string


cop_pn_count = 5000
cop_pn_dev_date = datetime.date(2025, 6, 12)

a003_bw_logger = logging.getLogger(serve.Apps.A003SmartAlerts.bw_logger_name)
from xylem.settings import EMAIL_HOST_USER, XYLEM_MODE, XYLEM_MODE_DIC

def send_cop_part_number_alerts():
    while True:
        try:
            part_numbers = serve.get_part_numbers(product_category=serve.ProductCategory.seat_belt)
            for pn in part_numbers:
                # Get last saved COP record
                last_cop = CopPartnumber.objects.filter(part_number_i=pn).order_by('-datetime').first()
                if last_cop:
                    # Count PQ from the last COP datetime
                    last_dt = last_cop.datetime
                    pq_sum = ProductionChangeOvers.objects.filter(
                        part_number_i=pn,
                        start_time__gt=last_dt
                    ).aggregate(total_pq=Sum("pq"))
                else:
                    # First time, count from defined baseline date
                    pq_sum = ProductionChangeOvers.objects.filter(
                        part_number_i=pn,
                        start_time__date__gt=cop_pn_dev_date
                    ).aggregate(total_pq=Sum("pq"))
                pq = pq_sum['total_pq'] or 0
                # Threshold crossed (example 5000)
                if pq >= cop_pn_count:
                    # NOW create new entry because this is a new 5000 cycle
                    cop_pn_obj = CopPartnumber.objects.create(part_number_i=pn)
                    # Send alert
                    to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a003_cop_pn_alert_mail)
                    subject = "X-A008 Info: Initiate COP Process"
                    html_content = render_to_string('a003/cop_pn_mail.html', {'cop_pn_obj': cop_pn_obj})
                    serve.send_mail(
                        app_name=serve.an_home_schemer,
                        subject=subject,
                        to_list=to_list,
                        html_content=html_content
                    )
        except Exception as e:
            a003_bw_logger.error("Exception occurred in COP alert loop", exc_info=True)
        time.sleep(10)

if XYLEM_MODE == XYLEM_MODE_DIC["development_mode"]:
    pass
	# serve.run_as_thread(send_cop_part_number_alerts)
	
elif XYLEM_MODE == XYLEM_MODE_DIC["testing_mode"]:
	serve.run_as_thread(send_cop_part_number_alerts)
	
elif XYLEM_MODE == XYLEM_MODE_DIC["deployment_mode"]:
	serve.run_as_thread(send_cop_part_number_alerts)
