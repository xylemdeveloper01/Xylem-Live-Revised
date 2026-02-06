import logging, datetime, copy,base64
from django.utils import timezone

from xylem_apps.a000_xylem_master.background_works import xr_websocket
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import UserProfile
from django.contrib.auth.hashers import check_password

xr_handler_logger = logging.getLogger(serve.xylem_remote_handler_log_name)
app = serve.Apps.A000XylemMaster


def xr_recv_handler():
    while True:
        # Process the received data from the queue
        xr_data = app.xrh_app_queue.get()
        serve.run_as_thread(process_xr_login_data, args=(xr_data,))


def encrypt_text_base64(plain_text):
    return base64.b64encode(plain_text.encode()).decode()


def decrypt_text_base64(encrypted_text):
    return base64.b64decode(encrypted_text.encode()).decode() 


def process_xr_login_data(xr_data):
    try:
        s000_service = serve.XylemRemoteServices.S000XylemRemoteMaster
        if xr_data["service_code"] in s000_service.codes:
            progress_level = serve.get_progress_level_by_key(xr_data["progress_key"])
            service_name = s000_service.name
            del_session = None         
            if progress_level == s000_service.Progress.xylem_login_validation.code:
                username = xr_data.get("username")
                password = xr_data.get("password")
                encrypted = decrypt_text_base64(password)
                user = UserProfile.objects.filter(username=username).first()                              
                if user is None:  
                    xr_data["validation"] = s000_service.Validation.invalid_xylem_user.code                     
                else:
                    if not check_password(encrypted, user.password):
                        xr_data["validation"] = s000_service.Validation.invalid_credentials.code 
                    else:
                        if user.is_active == None:                        
                            xr_data["validation"] = s000_service.Validation.ifs_approval_pending.code 
                        elif user.is_active == False:                                                                                                                    
                            xr_data["validation"] = s000_service.Validation.ifs_approval_denied.code 
                        elif user.is_active == True:                                                
                            xr_data["validation"] = s000_service.Validation.valid_xylem_user.code
                            user_dict={}          
                            user_dict["first_name"] = user.first_name 
                            user_dict["last_name"] = user.last_name
                            user_dict["username"] = user.username
                            user_dict["gender"] = user.gender_i.name
                            user_dict["email"] = user.email
                            user_dict["dept"] = user.dept_i.name
                            user_dict["designation"] = user.designation_i.name
                            user_dict["plant_location"] = user.plant_location_i.name
                            xr_data["user_data"] = user_dict                                                                      
                              
            del_session = True  
            xr_websocket.service_dict[service_name][xr_data["session_key"]] = {
                "xr_data": copy.deepcopy(xr_data),
                "last_activity": datetime.datetime.now(),
                "del_session": del_session
            }
            xr_websocket.ws_send_queue.put(xr_data)
            xr_handler_logger.info(
                f"{s000_service.get_progress_description(progress_level)} "
                f"{s000_service.get_validation_description(xr_data['validation'])} "
                f"{xr_data['session_key']}"
            )
    except Exception as e:
        xr_handler_logger.error("Exception occurred", exc_info=True)


serve.run_as_thread(xr_recv_handler)
