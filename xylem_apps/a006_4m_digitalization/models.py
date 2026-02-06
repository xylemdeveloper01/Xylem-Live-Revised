from django.db import models
from xylem_apps.a000_xylem_master.models import Icodes,UserProfile
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master import serve 

fm_before_desc_min_len = 100
fm_after_desc_min_len = 100
fm_change_desc_min_len = 100
approval_response_min_len = 10
fm_before_desc_max_len = 500
fm_after_desc_max_len = 500
fm_change_desc_max_len = 500
approval_response_max_len = 150


# Create your models here.
class FourMFormModel(models.Model):
    four_m_point_i = models.ForeignKey(Icodes, verbose_name=_('4M Point'), on_delete=models.PROTECT, related_name='a006_fmfm_fmp', db_constraint=False)
    fm_change_datetime = models.DateTimeField()
    fm_before_desc = models.CharField(max_length=fm_before_desc_max_len)
    fm_after_desc = models.CharField(max_length=fm_after_desc_max_len)
    fm_change_desc = models.CharField(max_length=fm_change_desc_max_len)
    fm_status = models.BooleanField(null=True)
    supplier_rel_chng = models.BooleanField()
    raised_datetime = models.DateTimeField(auto_now_add=True)
    raised_user = models.ForeignKey(UserProfile, verbose_name=_('Raised User'), on_delete=models.PROTECT, related_name='a006_fmfm_ru', db_constraint=False)
    remote_token = models.UUIDField(default=serve.generate_uuid_token32, verbose_name=_('Random UUID'))


class FourMMapping(models.Model):
    four_m_form_ref = models.ForeignKey(FourMFormModel, verbose_name=_('4M Form Reference'), on_delete=models.PROTECT, related_name='a006_fmm_fr')
    mapped_i = models.ForeignKey(Icodes, verbose_name=_('Mapped Icode Data'), on_delete=models.PROTECT, related_name='a006_fmm_mi', db_constraint=False)


class FourMApprovals(models.Model):
    four_m_form_ref = models.ForeignKey(FourMFormModel, verbose_name=_('4M Form Reference'), on_delete=models.PROTECT, related_name='a006_fma_fr')
    approval_needed_dept_i = models.ForeignKey(Icodes, verbose_name=_('Approval Requested Department Icode Data'), on_delete=models.PROTECT, related_name='a006_fma_rd', db_constraint=False)
    response = models.BooleanField(null=True)
    response_desc = models.CharField(max_length=approval_response_max_len, null=True)
    responded_user = models.ForeignKey(UserProfile, verbose_name=_('Responded User'), on_delete=models.PROTECT, related_name='a006_fma_ru', db_constraint=False, null=True)
    response_datetime = models.DateTimeField(null=True)
    approval_mode = models.ForeignKey(Icodes, verbose_name=_('Approval Mode'), on_delete=models.PROTECT, related_name='a006_fma_am', db_constraint=False, null=True)
