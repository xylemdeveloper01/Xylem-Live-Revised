import logging, time, threading,datetime, tempfile,os
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.staticfiles import finders
from django.db.models import Max, Q, F
from xhtml2pdf import pisa
from io import BytesIO

from xylem_apps.a000_xylem_master import serve 
from xylem_apps.a000_xylem_master .models import Icodes, UserProfile
from xylem_apps.a006_4m_digitalization .models import FourMFormModel,FourMApprovals,FourMMapping

xylem_logo_path = finders.find('assets/images/xylem-logo.png')
zf_rane_logo_path = finders.find('assets/images/ZF_Rane.png')

a006_logger = logging.getLogger(serve.an_4m_digitalization)


def send_four_m_mail(four_m_form_id):  
    four_m_form = FourMFormModel.objects.get(id=four_m_form_id)
    mapped_items = FourMMapping.objects.filter(four_m_form_ref=four_m_form)
    product_category_id = (mapped_items.first().mapped_i.icode // serve.IcodeSplitup.product_category["period"]) * serve.IcodeSplitup.product_category["period"]
    mapped_items_ls = list(mapped_items.values_list("mapped_i", flat=True))
    child_part_numbers = {}
    if four_m_form.supplier_rel_chng:
        child_part_numbers = Icodes.objects.filter(Q(icode__in=mapped_items_ls) & Q(icode__in=serve.get_child_part_numbers(product_category_id=product_category_id))).order_by("icode")	
    app_linked_token = serve.get_app_linked_token(str(four_m_form.remote_token), app=serve.Apps.A0064MDigitalization)   
    four_m_app_dept = list(FourMApprovals.objects.filter(four_m_form_ref=four_m_form).values_list('approval_needed_dept_i', flat=True).distinct())  
    four_m_data_dict = {
        'four_m_form': four_m_form,
        'production_lines': Icodes.objects.filter(Q(icode__in=mapped_items_ls) & Q(icode__in=serve.get_production_lines(product_category_id=product_category_id))).order_by("icode"),
        'product_models': Icodes.objects.filter(Q(icode__in=mapped_items_ls) & Q(icode__in=serve.get_product_models(product_category_id=product_category_id))).order_by("icode"),
        'part_numbers':  Icodes.objects.filter(Q(icode__in = mapped_items_ls) & Q(icode__in=serve.get_part_numbers(product_category_id=product_category_id))).order_by("icode"),
        'approval_needed_dept': list(serve.get_icode_objects(four_m_app_dept)),
        'child_part_numbers': child_part_numbers,
        'xr_approve_url': serve.xylem_remote_approval_url.format(token = app_linked_token, response = serve.XylemRemoteServices.S001XylemRemoteApproval.UserResponse.approve.code),
        'xr_reject_url': serve.xylem_remote_approval_url.format(token = app_linked_token, response = serve.XylemRemoteServices.S001XylemRemoteApproval.UserResponse.reject.code),
        'xylem_app_url': serve.fourm_approval_url.format(fourm_id = four_m_form.id)
    }
    html_content_for_pdf = render_to_string('a006/fourm_form_mail_pdf.html',
        {
            'four_m_data_dict': four_m_data_dict,
            'xylem_logo_path': xylem_logo_path,
            'zf_rane_logo_path': zf_rane_logo_path
        }
    )
    pdf_file = BytesIO()
    create_pdf = pisa.CreatePDF(html_content_for_pdf, dest=pdf_file)    
    pdf_file.seek(0)  # Reset before write   

    temp_dir = os.path.join(settings.MEDIA_ROOT, "a006")
    os.makedirs(temp_dir, exist_ok=True)  # Auto-create
    file_name = f"4M_Form_X-a006-{four_m_form.id}.pdf"
    temp_pdf_path = os.path.join(temp_dir, file_name)  
    with open(temp_pdf_path, "wb") as f: # Save to file
        f.write(pdf_file.read())  
    if create_pdf.err:
        a006_logger.error(f"Failed to generate PDF for 4M Form with ID {four_m_form.id}")  

    app_mail_list_of_four_m = list(
        UserProfile.objects.filter(is_active=True,email__endswith='@ranegroup.com').filter
        (
            Q(dept_i__in=four_m_app_dept,designation_i__gte=serve.Apps.A0064MDigitalization.min_approver_designation) |
            Q(dept_i=serve.Depts.Development_team.icode)
        ).values_list('email', flat=True).distinct())
    serve.send_mail(
        app_name = serve.an_4m_digitalization,
        subject = f"X-A006 Info : 4M Change Approval Request" ,
        to_list = app_mail_list_of_four_m,       
        html_content =  render_to_string('a006/fourm_form_mail.html',{'four_m_data_dict': four_m_data_dict}),            
        attachments_path_list = [temp_pdf_path]
    ) 
    return {
        "status": "success",
        "four_m_id": four_m_form.id,
        "message": "4M approval mail sent successfully"
    }
