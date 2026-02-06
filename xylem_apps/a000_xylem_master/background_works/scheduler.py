import time, schedule, logging
from xylem_apps.a000_xylem_master import serve


a000_bw_logger = logging.getLogger(serve.Apps.A000XylemMaster.bw_logger_name)

def schedule_thread():
    logged_flag=False
    while True:
        try:
            while True:  
                schedule.run_pending()
                if logged_flag:
                    logged_flag=False
                time.sleep(serve.scheduler_delay)
        except Exception as e:
            if not logged_flag:
                a000_bw_logger.error("Exception occurred", exc_info=True)
                logged_flag=True
            time.sleep(serve.error_wait)

serve.run_as_thread(schedule_thread)