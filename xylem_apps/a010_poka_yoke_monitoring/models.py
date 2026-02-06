import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master.models import Icodes, UserProfile, PyPsMapping

# Create your models here.
class PokaYokeInspections(models.Model):
    pyps_map = models.ForeignKey(PyPsMapping, verbose_name=_('Poka Yoke & Production Station Mapping'), on_delete=models.DO_NOTHING, related_name='a010_pi_pm', db_constraint=False)
    inspection_status = models.BooleanField(null=True)
    inspection_datetime = models.DateTimeField(auto_now_add=True, null=True)
    inspection_due_date = models.DateField()
    inspected_user = models.ForeignKey(UserProfile, verbose_name=_('Inspected User'), on_delete=models.PROTECT, related_name='a010_pi_iu', db_constraint=False, null=True)
   