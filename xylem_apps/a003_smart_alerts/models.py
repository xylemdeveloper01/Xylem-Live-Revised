from django.db import models
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master.models import Icodes


class CopPartnumber(models.Model):
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='a007_mrq_pn', db_constraint=False, null=True)
    pq_offset = models.PositiveIntegerField(verbose_name=_('Production Quantity Offset'),null=True)
    datetime = models.DateTimeField(auto_now=True)


class WebPulligNGAlerts(models.Model):
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='a003_wpn_pl', db_constraint=False)
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='a003_wpn_pn', db_constraint=False, null=True)
    temp_pn = models.TextField(null=True)
    barcode_data =  models.TextField()
    part_description = models.TextField(null=True)
    datetime = models.DateTimeField(auto_now=True)


class FrictionWeldingAlerts(models.Model):
    where_id_i = models.ForeignKey(Icodes, verbose_name=_('Where ID'), on_delete=models.PROTECT, related_name='a003_fwa_wrid', db_constraint=False)
    part_barcode_data =  models.TextField()
    mgg_barcode_data = models.TextField()
    part_description = models.TextField()
    ng_description = models.TextField()
    logged_dt = models.DateTimeField()
    action_taken = models.TextField(null=True)
    datetime = models.DateTimeField(auto_now=True)


class FrictionWeldingLastReadData(models.Model):
    where_id_i = models.OneToOneField(Icodes, verbose_name=_('Where ID'), on_delete=models.PROTECT, related_name='a003_fwlrd_wrid', db_constraint=False)
    last_checked_logged_dt = models.DateTimeField()
    last_checked_modified_dt = models.DateTimeField()
