from django import forms
from django.utils.translation import gettext_lazy as _

from xylem_apps.a000_xylem_master.forms import IcodesModelChoiceField
from xylem_apps.a000_xylem_master import serve


class RejectionReworkEntryForm(forms.Form):
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select( attrs = { 'class' : 'form-control', 'id':'rre_form_id_product_category', 'autofocus': True, } ),
    )    
    production_line = IcodesModelChoiceField(
        label = _('Select Production Line '),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select( attrs = {'class' : 'form-control', 'id':'rre_form_id_production_line', })
    )
    production_station = IcodesModelChoiceField(
        label = _('Select Production Stations '),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select( attrs = {'class' : 'form-control', 'id':'rre_form_id_production_station', })
    )
    model = IcodesModelChoiceField(
        label = _('Select Models'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'rre_form_id_product_model', })
    )
    part_number = IcodesModelChoiceField(
        label = _('Select Part Number'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select( attrs = { 'class' : 'form-control', 'id':'rre_form_id_part_number', })
    )
    rejection_reason = IcodesModelChoiceField(
        label = _('Select rejection reason'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select( attrs = { 'class' : 'form-control', 'id':'rre_form_id_rejection_reasons', })
    )
    part_status = IcodesModelChoiceField(
        label = _('Select part status'),
        label_suffix = '',
        queryset=serve.get_part_status_rejection_and_rework(),
        widget = forms.Select( attrs = { 'class' : 'form-control', 'id':'rre_form_id_part_status', })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_category' in self.data:
            self.fields['production_line'].queryset = serve.get_production_lines(product_category_id=self.data.get('product_category'))         
            self.fields['production_station'].queryset = serve.get_production_stations(production_line_id=self.data.get('production_line'))
            self.fields['model'].queryset = serve.get_product_models_of_ps(production_station_id=self.data.get('production_station'))
            self.fields['part_number'].queryset = serve.get_part_numbers_of_model(model_id=self.data.get('model'))
            self.fields['rejection_reason'].queryset = serve.get_rejection_reasons(product_category_id=self.data.get('product_category'))