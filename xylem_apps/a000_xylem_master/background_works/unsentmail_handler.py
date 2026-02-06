import time, requests, ast,logging, os
from django.core.mail import EmailMultiAlternatives

from xylem.settings import EMAIL_HOST_USER
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import UnsentMails

mail_handler_logger = logging.getLogger(serve.mail_handler_log_name)

def checking_internet_connection_and_resend_mails():
    while True:
        try:
            # Check internet
            requests.get("https://www.google.com", timeout=5)
            unsent_mails = UnsentMails.objects.filter(status=False)
            for mail in unsent_mails:
                text_content = mail.text_content or ""
                html_content = mail.html_content or ""
                to_list = ast.literal_eval(mail.to_list) if mail.to_list else []
                cc_list = ast.literal_eval(mail.cc_list) if mail.cc_list else []
                bcc_list = ast.literal_eval(mail.bcc_list) if mail.bcc_list else []
                attachments_list = (ast.literal_eval(mail.attachments_path_list) if mail.attachments_path_list else [])
                msg = EmailMultiAlternatives(
                    subject=f"{mail.subject} (Delayed)",
                    body = text_content + "\n\nThis mail was delayed due to internet connection issues in Xylem server.",
                    from_email=EMAIL_HOST_USER,
                    to=to_list,
                    cc=cc_list,
                    bcc=bcc_list
                )
                if html_content:
                    msg.attach_alternative(html_content, "text/html")
                attached_files = []
                # Attach files ONLY if present
                for file_path in attachments_list:
                    if os.path.exists(file_path):
                        try:
                            msg.attach_file(file_path)
                            attached_files.append(file_path)
                        except Exception as e:
                            mail_handler_logger.error(f"Attachment error for {file_path}: {e}")
                    else:
                        mail_handler_logger.warning(f"Attachment missing (skipped): {file_path}")               
                msg.send()
                #  Delete files only if they were attached
                for file_path in attached_files:
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        mail_handler_logger.warning(f"Failed to delete attachment {file_path}: {e}")
                mail.status = True
                mail.save()
                mail_handler_logger.info(f"{mail.subject} (Delayed) sent successfully, "f"Actual time: {mail.created_at}")
        except requests.RequestException:
            time.sleep(serve.error_wait)


serve.run_as_thread(checking_internet_connection_and_resend_mails)