from django.db import models
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master.models import Icodes, UserProfile

minutes_period = 2 #should be the factors of 60 and the maximum is 15
max_minute_period = int(60/minutes_period)

pq_hp_list = []
for i in range(24):
    for j in range(max_minute_period):
        pq_hp_list.append(f'pq_H{i}P{j}')

# Create your models here.
class ProductionData(models.Model):
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='a007_pd_pl', db_constraint=False)
    for i in pq_hp_list:
        locals()[i] = models.PositiveSmallIntegerField(null=True)
    date = models.DateField()


class IdleEvents(models.Model):
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='a007_ie_pl', db_constraint=False)
    where_id_i = models.ForeignKey(Icodes, verbose_name=_('Where ID'), on_delete=models.PROTECT, related_name='a007_ie_wrid', db_constraint=False, null=True)
    what_id_i = models.ForeignKey(Icodes, verbose_name=_('What ID'), on_delete=models.PROTECT, related_name='a007_ie_whid', db_constraint=False, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    acceptance = models.BooleanField(null=True)
    responded_user = models.ForeignKey(UserProfile, verbose_name=_('Responded User'), on_delete=models.PROTECT, related_name='a007_ie_ru', db_constraint=False, null=True)


class ProductionChangeOvers(models.Model):
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='a007_pco_pl', db_constraint=False)
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='a007_pco_pn', db_constraint=False, null=True)
    temp_pn = models.CharField(max_length=30, null=True)
    pq = models.PositiveSmallIntegerField(null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)


class OEEData(models.Model):
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='a007_od_pl', db_constraint=False)
    date = models.DateField()
    shift = models.ForeignKey(Icodes, verbose_name=_('Shift'), on_delete=models.PROTECT, related_name='a007_od_s', db_constraint=False, null=True)
    oee = models.FloatField(verbose_name=_('OEE'))
    availability = models.FloatField(verbose_name=_('Availability'))
    performance = models.FloatField(verbose_name=_('Performance'))
    quality = models.FloatField(verbose_name=_('Quality'))
    avl_time = models.PositiveIntegerField(verbose_name=_('Available Time in seconds'))
    pdt = models.PositiveIntegerField(verbose_name=_('Planned Down Time in seconds'))
    updt = models.PositiveIntegerField(verbose_name=_('Unplanned Down Time in seconds'))
    pq_plan = models.PositiveSmallIntegerField(verbose_name=_('Production Quantity Plan'))
    pq_perf_plan = models.PositiveSmallIntegerField(verbose_name=_('Production Quantity Performance Plan'))
    pq_actual = models.PositiveSmallIntegerField(verbose_name=_('Production Quantity Actual'))
    pq_ok_p = models.PositiveSmallIntegerField(verbose_name=_('Production Quantity Ok parts'))
    tot_le = models.PositiveSmallIntegerField(verbose_name=_('Total Loss Events'))
    fm_le_where_i = models.ForeignKey(Icodes, verbose_name=_('First Major Loss Event\'s where id'), on_delete=models.PROTECT, related_name='a007_od_fm_wr_id', db_constraint=False, null=True)
    fm_le_what_i = models.ForeignKey(Icodes, verbose_name=_('First Major Loss Event\'s what id'), on_delete=models.PROTECT, related_name='a007_od_fm_wt_id', db_constraint=False, null=True)
    fm_le_it = models.PositiveIntegerField(verbose_name=_('First Major Loss Event\'s Idle time in seconds'), null=True)
    sm_le_where_i = models.ForeignKey(Icodes, verbose_name=_('Second Major Loss Event\'s where id'), on_delete=models.PROTECT, related_name='a007_od_sm_wr_id', db_constraint=False, null=True)
    sm_le_what_i = models.ForeignKey(Icodes, verbose_name=_('Second Major Loss Event\'s what id'), on_delete=models.PROTECT, related_name='a007_od_sm_wt_id', db_constraint=False, null=True)
    sm_le_it = models.PositiveIntegerField(verbose_name=_('Second Major Loss Event\'s Idle time in seconds'), null=True)
    tm_le_where_i = models.ForeignKey(Icodes, verbose_name=_('Third Major Loss Event\'s where id'), on_delete=models.PROTECT, related_name='a007_od_tm_wr_id', db_constraint=False, null=True)
    tm_le_what_i = models.ForeignKey(Icodes, verbose_name=_('Third Major Loss Event\'s what id'), on_delete=models.PROTECT, related_name='a007_od_tm_wt_id', db_constraint=False, null=True)
    tm_le_it = models.PositiveIntegerField(verbose_name=_('Third Major Loss Event\'s Idle time in seconds'), null=True)


class ProductionPlan(models.Model):
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='a007_pp_pl', db_constraint=False)
    plan_date = models.DateField()
    shift = models.ForeignKey(Icodes, verbose_name=_('Shift'), on_delete=models.PROTECT, related_name='a007_pp_s', db_constraint=False)
    planned_qty = models.PositiveSmallIntegerField(verbose_name=_('Production Planned Quantity'))
    revision = models.PositiveSmallIntegerField(verbose_name=_('Production Plan Revision Number'))
    created_user = models.ForeignKey(UserProfile, verbose_name=_('Changeuser'), on_delete=models.PROTECT, related_name='a007_pp_cu', db_constraint=False)
    added_datetime = models.DateTimeField(auto_now=True)


class ProductionPlanMaxRef(models.Model):
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='a007_ppmr_pl', db_constraint=False)
    plan_date = models.DateField()
    shift = models.ForeignKey(Icodes, verbose_name=_('Shift'), on_delete=models.PROTECT, related_name='a007_ppmr_s', db_constraint=False)
    production_plan_max = models.PositiveSmallIntegerField(verbose_name=_('Production Plan max for the shift'))