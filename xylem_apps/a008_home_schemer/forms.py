from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from xylem_apps.a000_xylem_master.forms import MaxFileSizeValidator

from .models import event_caption_min_len, event_caption_max_len, event_desc_min_len, event_desc_max_len    
        

class EventAdditionForm(forms.Form):
    event_image = forms.ImageField(
        label = _('Upload image of the event'),
        label_suffix = '',
        help_text='Note : Allowed formats - JPG, JPEG, PNG. Maximum file size - 10MB',
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif']), 
            MaxFileSizeValidator(10 * 1024 * 1024)  # 10 MB in bytes
        ]
    )
    caption = forms.CharField(
        label = _('Give a caption for the event'),
        label_suffix = '',
        widget = forms.Textarea(attrs = { 'class' : 'form-control', 'rows':2, 'minlength': event_caption_min_len, 'maxlength': event_caption_max_len, }),
    )
    description = forms.CharField(
        label = _('Describe your memories'),
        label_suffix = '',
        widget = forms.Textarea(attrs = { 'class' : 'form-control', 'rows':2, 'minlength': event_desc_min_len, 'maxlength': event_desc_max_len, }),
    )