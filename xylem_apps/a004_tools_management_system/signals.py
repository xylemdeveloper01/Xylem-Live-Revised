import logging
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


from xylem.settings import EMAIL_HOST_USER
from xylem_apps.a000_xylem_master import serve


from .models import ToolHistoryLog


a004_logger = logging.getLogger(serve.an_tools_management_system)


def send_boost_mail(tool_history_log):
    to_list = serve.get_mail_ids_list_of_mail(serve.Mails.a004_tool_life_boost_mail)
    subject = "X - A004 Info : Tool Life Boosted"
    html_content = render_to_string('a004/tool_life_boost_mail.html', {'tool_history_log': tool_history_log,})
    serve.send_mail(app_name = serve.an_tools_management_system, subject = subject, to_list = to_list, html_content = html_content)


@receiver(post_save, sender=ToolHistoryLog)
def trigger_boost_mail(sender, instance, created, **kwargs):
    serve.run_as_thread(send_boost_mail, args=(instance,))
