from django.db import models
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master.models import Icodes, UserProfile


# Create your models here.
class RejectionReworkEntryData(models.Model):
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='a002_rre_pn', db_constraint=False)
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='a002_rre_pl', db_constraint=False)
    production_station_i = models.ForeignKey(Icodes, verbose_name=_('Production Station'), on_delete=models.PROTECT, related_name='a002_rre_ps', db_constraint=False)
    rejection_reason_i = models.ForeignKey(Icodes, verbose_name=_('Rejection Reason'), on_delete=models.PROTECT, related_name='a002_rre_rr', db_constraint=False)
    part_status_i = models.ForeignKey(Icodes, verbose_name=_('Part Status'), on_delete=models.PROTECT, related_name='a002_rre_ps_rr', db_constraint=False)
    barcode_data = models.CharField(max_length=50)
    description_i = models.ForeignKey(Icodes, verbose_name=_('Description'), on_delete=models.PROTECT, related_name='a002_rre_d', null=True, db_constraint=False)
    booked_datetime = models.DateTimeField(auto_now_add=True)
    booked_user = models.ForeignKey(UserProfile, verbose_name=_('Booked by'), on_delete=models.PROTECT, related_name='a002_rre_bb', db_constraint=False)


class PackingInterlockData(models.Model):
    entry_ref = models.ForeignKey(RejectionReworkEntryData, verbose_name=_('Entry data Reference'), on_delete=models.PROTECT, related_name='a002_pi_edr')
    barcode_data = models.CharField(max_length=50)
    part_status_i = models.ForeignKey(Icodes, verbose_name=_('Part Status'), on_delete=models.PROTECT, related_name='a002_pi_ps_rr', db_constraint=False)
    datetime = models.DateTimeField()
