from django.db import models
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master.models import UserProfile

event_caption_min_len=10
event_caption_max_len=100
event_desc_min_len=30
event_desc_max_len=500


# Create your models here.
class EventData(models.Model):
    event_image = models.ImageField(verbose_name=_('Image of the event'), upload_to='a008/event_images/')
    caption = models.CharField(verbose_name=_('Caption of the event'), max_length=event_caption_max_len)  
    description = models.CharField(verbose_name=_('Description of the event'), max_length=event_desc_max_len)  
    added_datetime = models.DateTimeField(auto_now=True)
    added_user = models.ForeignKey(UserProfile, verbose_name=_('added User'), related_name='a008_ed_au', on_delete=models.PROTECT, db_constraint=False)