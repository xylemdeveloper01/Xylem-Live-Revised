from django.db import models
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master.models import Icodes

minutes_period = 5 #should be the factors of 60 and the maximum is 30
max_minute_period = int(60/minutes_period)

twf_hp_list = []
for i in range(24):
    for j in range(max_minute_period):
        twf_hp_list.append(f'tf_H{i}P{j}')


# Create your models here.
class WaterFlowData(models.Model):
    flow_meter_i = models.ForeignKey(Icodes, verbose_name=_('Flow Meter'), on_delete=models.PROTECT, related_name='a009_wfd_fm', db_constraint=False)
    for i in twf_hp_list:
        locals()[i] = models.FloatField(null=True) # in liters
    date = models.DateField()
    

class WaterFlowCumData(models.Model):
    flow_meter_i = models.ForeignKey(Icodes, verbose_name=_('Flow Meter'), on_delete=models.PROTECT, related_name='a009_wfcd_fm', db_constraint=False)
    date = models.DateField()
    twf = models.FloatField() # in liters


class WaterFlowLastReadData(models.Model):
    flow_meter_i = models.OneToOneField(Icodes, verbose_name=_('Flow Meter'), on_delete=models.PROTECT, related_name='a009_wflrd_fm', db_constraint=False,  primary_key=True)
    last_updated_dt = models.DateTimeField(auto_now=True)
    tf = models.FloatField() # in kilo liters