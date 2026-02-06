from django.db import models
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master.models import Icodes, UserProfile, TPsMapping
from xylem_apps.a006_4m_digitalization.models import FourMFormModel
from xylem_apps.a007_oee_monitoring.models import ProductionChangeOvers

action_taken_min_len = 75
action_taken_max_len = 500

# Create your models here.
class ToolHistoryLog(models.Model):  
    tps_map = models.ForeignKey(TPsMapping, verbose_name=_('Tool & Production Station Mapping'), on_delete=models.PROTECT, related_name='a004_thl_tm', db_constraint=False)
    boosted_change_over = models.ForeignKey(ProductionChangeOvers, verbose_name=_('Boosted Change Over'), on_delete=models.PROTECT, related_name='a004_thl_tco', null=True, db_constraint=False)
    reason_for_change = models.ForeignKey(Icodes, verbose_name=_('Reason for tool change'), on_delete=models.PROTECT, related_name='a004_thl_rfc', db_constraint=False)
    four_m_form_ref = models.ForeignKey(FourMFormModel, verbose_name=_('boosted Change Over'), on_delete=models.PROTECT, related_name='a004_thl_fmfr', db_constraint=False)
    pre_avl_life = models.IntegerField(verbose_name=_('Available Life before Boost'))
    produced_pq = models.IntegerField(verbose_name=_('Produced production quantity of the tool'))
    pq_offset = models.PositiveIntegerField(verbose_name=_('Production Quantity Offset'))
    action_taken = models.CharField(max_length=action_taken_max_len)
    boosted_user = models.ForeignKey(UserProfile, verbose_name=_('Boosted User'), on_delete=models.PROTECT, related_name='a004_thl_fmfr', db_constraint=False)
    boosted_time = models.DateTimeField(auto_now=True)


class ToolAlert(models.Model):  
    tps_map = models.OneToOneField(TPsMapping, verbose_name=_('Tool & Production Station Mapping'), on_delete=models.PROTECT, related_name='a004_ta_tm', primary_key=True, db_constraint=False)
    alert_date = models.DateField()