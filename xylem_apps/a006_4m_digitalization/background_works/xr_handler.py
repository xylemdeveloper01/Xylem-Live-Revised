import logging, datetime, copy
from django.utils import timezone

from xylem_apps.a000_xylem_master.background_works import xr_websocket
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom_not_as_decorator
from xylem_apps.a006_4m_digitalization.models import FourMFormModel, FourMApprovals, approval_response_min_len, approval_response_max_len

xr_handler_logger = logging.getLogger(serve.xylem_remote_handler_log_name)
app = serve.Apps.A0064MDigitalization


def xr_recv_handler():
    while True:
        # Process the received data from the queue
        xr_data = app.xrh_app_queue.get()
        serve.run_as_thread(process_xr_app_login_data, args=(xr_data,))
    

def process_xr_app_login_data(xr_data):
    try:
        s001_service = serve.XylemRemoteServices.S001XylemRemoteApproval
        if xr_data["service_code"] in s001_service.codes:
            progress_level = serve.get_progress_level_by_key(xr_data["progress_key"])
            app, token = serve.extract_app_linked_token(xr_data["token"])
            four_m_forms = FourMFormModel.objects.filter(remote_token=token)
            service_name = s001_service.name
            user = serve.get_user_object_by_mail(xr_data["user_email"])
            del_session = None
            if progress_level == s001_service.Progress.validate_form.code:
                if four_m_forms.exists():
                    xr_data["validation"] = s001_service.Validation.ok.code
                else:
                    xr_data["validation"] = s001_service.Validation.invalid_form.code
                    del_session = True
            elif progress_level == s001_service.Progress.validate_form_status.code:
                four_m_form = four_m_forms.first()
                if four_m_form.fm_status is None:
                    response = four_m_form.a006_fma_fr.filter(
                        approval_needed_dept_i = user.dept_i, response__isnull = False
                    )
                    if response.exists():
                        responded_by = response.first().responded_user
                        if user == responded_by:
                            xr_data["validation"] = s001_service.Validation.already_approved_by_you.code
                        else:
                            xr_data["validation"] = s001_service.Validation.already_approved_by_other.code
                            xr_data["responded_by"] = serve.get_user_display_format(user=responded_by, with_dept=True)
                    else:
                        xr_data["validation"] = s001_service.Validation.ok.code
                elif four_m_form.fm_status:
                    responded_by = four_m_form.a006_fma_fr.filter(
                        approval_needed_dept_i = user.dept_i,
                    ).first().responded_user
                    if user == responded_by:
                        xr_data["validation"] = s001_service.Validation.already_approved_by_you.code
                    else:
                        xr_data["validation"] = s001_service.Validation.already_approved_by_other.code
                        xr_data["responded_by"] = serve.get_user_display_format(user=responded_by, with_dept=True)
                    del_session = True
                else:
                    responded_by = four_m_form.a006_fma_fr.filter(response = False).first().responded_user
                    if user == responded_by:
                        xr_data["validation"] = s001_service.Validation.already_rejected_by_you.code
                    else:
                        xr_data["validation"] = s001_service.Validation.already_rejected_by_other.code
                        xr_data["responded_by"] = serve.get_user_display_format(user=responded_by, with_dept=True)
                    del_session = True               
            elif progress_level == s001_service.Progress.validate_user.code:
                four_m_form = four_m_forms.first()
                appr_elems = FourMApprovals.objects.filter(four_m_form_ref=four_m_form, approval_needed_dept_i=user.dept_i, response = None)
                if appr_elems.exists():
                    user_eligibility = user_passes_test_custom_not_as_decorator(
                        user = user, 
                        depts_with_min_designation_as_list = (
                            [serve.PlantLocations.SP_Koil, serve.Depts.All_depts, serve.Designations.Assistant_Manager],
                            [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
                            [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]
                        )
                    )
                    if user_eligibility:
                        appr_elem = appr_elems.first()
                        if appr_elem.response is None: 
                            xr_data["validation"] = s001_service.Validation.ok.code
                            xr_data["response_min_len"] = approval_response_min_len
                            xr_data["response_max_len"] = approval_response_max_len
                        else:
                            xr_data["validation"] = s001_service.Validation.invalid_request.code
                            del_session = True
                    else:
                        xr_data["validation"] = s001_service.Validation.invalid_user.code
                        del_session = True
                else:
                    xr_data["validation"] = s001_service.Validation.invalid_user_dept.code
                    del_session = True
            elif progress_level == s001_service.Progress.submit_response.code:
                four_m_form = four_m_forms.first()
                if four_m_form.fm_status is None:
                    appr_elem = four_m_form.a006_fma_fr.filter(approval_needed_dept_i = user.dept_i).first()
                    if appr_elem.response is None:
                        if int(xr_data["response"]) == s001_service.UserResponse.approve.code:
                            appr_elem.response = True
                        else:
                            appr_elem.response = False
                            four_m_form.fm_status = False
                            four_m_form.save()
                        appr_elem.response_desc = xr_data["response_desc"]
                        appr_elem.responded_user = user
                        appr_elem.response_datetime = timezone.now()
                        appr_elem.approval_mode = serve.ApprovalModes.xylem_remote_site
                        appr_elem.save()
                        if all(FourMApprovals.objects.filter(four_m_form_ref = four_m_form).values_list('response', flat=True)):
                            four_m_form.fm_status = True
                            four_m_form.save()
                        xr_data["validation"] = s001_service.Validation.ok.code
                    else:
                        responded_by = appr_elem.responded_user
                        if user == responded_by:
                            xr_data["validation"] = s001_service.Validation.already_approved_by_you_recently.code
                        else:
                            xr_data["validation"] = s001_service.Validation.already_approved_by_other_recently.code
                            xr_data["responded_by"] = serve.get_user_display_format(user=responded_by, with_dept=True)
                elif four_m_form.fm_status:
                    responded_by = four_m_form.a006_fma_fr.filter(
                        approval_needed_dept_i = user.dept_i,
                    ).first().responded_user
                    if user == responded_by:
                        xr_data["validation"] = s001_service.Validation.already_approved_by_you_recently.code
                    else:
                        xr_data["validation"] = s001_service.Validation.already_approved_by_other_recently.code
                        xr_data["responded_by"] = serve.get_user_display_format(user=responded_by, with_dept=True)
                else:
                    responded_by = four_m_form.a006_fma_fr.filter(response = False).first().responded_user
                    if user == responded_by:
                        xr_data["validation"] = s001_service.Validation.already_rejected_by_you_recently.code
                    else:
                        xr_data["validation"] = s001_service.Validation.already_rejected_by_other_recently.code
                        xr_data["responded_by"] = serve.get_user_display_format(user=responded_by, with_dept=True)
                del_session = True
            xr_websocket.service_dict[service_name][xr_data["session_key"]] = {
                "xr_data": copy.deepcopy(xr_data),
                "last_activity": datetime.datetime.now(),
                "del_session": del_session
            }
            xr_websocket.ws_send_queue.put(xr_data)
            xr_handler_logger.info(f"{s001_service.get_progress_description(progress_level)} {s001_service.get_validation_description(xr_data['validation'])} {xr_data['session_key']}")      
    except Exception as e:
        xr_handler_logger.error("Exception occurred", exc_info=True)


serve.run_as_thread(xr_recv_handler)
