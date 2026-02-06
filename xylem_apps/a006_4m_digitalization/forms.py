import datetime
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q
    
from xylem_apps.a000_xylem_master.forms import IcodesModelChoiceField, IcodesModelMultipleChoiceField
from xylem_apps.a000_xylem_master import serve
from .models import fm_before_desc_min_len,fm_after_desc_min_len,fm_change_desc_min_len,fm_before_desc_max_len,fm_after_desc_max_len,fm_change_desc_max_len


class FourMForm(forms.Form):
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'fm_form_id_product_category', 'autofocus': True, }),
    )
    production_lines = IcodesModelMultipleChoiceField(
        label = _('Select Production Lines '),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.SelectMultiple(attrs = { 'class' : 'form-control', 'id':'fm_form_id_production_lines', })
    )
    models = IcodesModelMultipleChoiceField(
        label = _('Select Models'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.SelectMultiple(attrs = { 'class' : 'form-control', 'id':'fm_form_id_product_models', })
    )
    part_numbers = IcodesModelMultipleChoiceField(
        label = _('Select Part Numbers'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.SelectMultiple(attrs = { 'class' : 'form-control', 'id':'fm_form_id_part_numbers', })
    )
    four_m_point = IcodesModelChoiceField(
        label = _('Select the changing point '),
        label_suffix = '',
        queryset=serve.get_four_m_points(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'fm_form_id_four_m_point', })
    )
    change_from = forms.DateTimeField(
        label = 'Change from date',
        label_suffix = '',
        widget = forms.DateTimeInput(attrs = { 'class' : 'form-control', 'type' : 'datetime-local', }),
    )
    before_desc = forms.CharField(
        label = 'Details of changing point before',
        label_suffix = '',
        widget = forms.Textarea(attrs = { 'class' : 'form-control',  'id':'fm_form_id_before_desc', "rows":5,
                                        "minlength":fm_before_desc_min_len, "maxlength": fm_before_desc_max_len, }),
    )
    after_desc = forms.CharField(
        label = 'Details of changing point after',
        label_suffix = '',
        widget = forms.Textarea(attrs = { 'class' : 'form-control',  'id':'fm_form_id_after_desc', "rows":5,
                                        "minlength":fm_after_desc_min_len, "maxlength": fm_after_desc_max_len, }),
    )
    change_desc = forms.CharField(
        label = 'Details of changing point',
        label_suffix = '',
        widget = forms.Textarea(attrs = { 'class' : 'form-control',  'id':'fm_form_id_chage_desc', "rows":5,
                                        "minlength":fm_change_desc_min_len, "maxlength": fm_change_desc_max_len, }),
    )
    supplier_rel_chng = IcodesModelChoiceField(
        label=_('Is supplier related change?'),
        label_suffix='',
        queryset=serve.get_yes_no_options(),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'fm_form_id_supplier_rel_chng'}),
    )
    child_part_numbers = IcodesModelMultipleChoiceField(
        label = _('Select child Part Number'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.SelectMultiple(attrs = { 'class' : 'form-control', 'id':'fm_form_id_child_part_numbers', })
    )
    approval_depts = IcodesModelMultipleChoiceField(
        label = _(f'Select Departments for the approval in addition to {serve.Depts.Inprocess_QA.name}, {serve.Depts.MFG.name} and Your Dept.'),
        queryset = serve.get_depts().filter(~Q(icode__in=[serve.Depts.Inprocess_QA.icode, serve.Depts.MFG.icode])),
        widget = forms.SelectMultiple(attrs = {'class' : 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['change_from'].widget.attrs.update(max=f"{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M')}")
        if 'product_category' in self.data:
            self.fields['production_lines'].queryset = serve.get_icode_objects(self.data.getlist('production_lines'))
            self.fields['models'].queryset = serve.get_icode_objects(self.data.getlist('models'))
            self.fields['part_numbers'].queryset = serve.get_icode_objects(self.data.getlist('part_numbers'))
            supplier_rel_chng = int(self.data.get('supplier_rel_chng'))
            if supplier_rel_chng == serve.Others.yes_option.icode:
                self.fields['child_part_numbers'].required = True
                self.fields['child_part_numbers'].queryset = serve.get_icode_objects(self.data.getlist('child_part_numbers'))
            else:
                self.fields['child_part_numbers'].required = False
    
    def user(self, user):
        self.fields['approval_depts'].queryset = self.fields['approval_depts'].queryset.filter(~Q(icode=user.dept_i.icode))