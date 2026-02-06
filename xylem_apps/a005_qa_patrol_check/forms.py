import datetime
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.forms import IcodesModelChoiceField


class ChecksheelLogModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.checksheet_name
    

class PlDSSelectionForm(forms.Form):
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset = serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id': 'plds_id_product_category', 'autofocus': True, }),
    )
    production_line = IcodesModelChoiceField(
        label = _('Select Production Line '),
        label_suffix = '',
        queryset = serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'plds_id_production_line', })
    )
    date = forms.DateField(
        label = _('Select date'),
        label_suffix = '',
        widget = forms.DateInput(attrs = { 'class' : 'form-control', 'type' : 'date', }),
    )
    shift = IcodesModelChoiceField(
        label = _('Select shift'),
        label_suffix = '',
        queryset = serve.get_shifts(),
        widget = forms.Select(attrs = { 'class' : 'form-control', })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs.update(max=f"{datetime.datetime.now().date()}")
        if 'product_category' in self.data:
            self.fields['production_line'].queryset = serve.get_icode_objects([self.data.get('production_line')])