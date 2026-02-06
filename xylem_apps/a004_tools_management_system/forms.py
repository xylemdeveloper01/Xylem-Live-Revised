from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError

from xylem_apps.a000_xylem_master.forms import IcodesModelChoiceField, PrependedTextInput
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a006_4m_digitalization.models import FourMFormModel, FourMMapping

from .models import action_taken_min_len, action_taken_max_len, ToolHistoryLog


class ToolLifeBoostForm(forms.Form):
    reason_for_change = IcodesModelChoiceField(
        label=_('Reason for Change'),
        label_suffix='',
        queryset=serve.get_tool_change_reasons(),
        widget=forms.Select(attrs={'class': 'form-control', 'autofocus': True,})
    )

    four_m_form_ref_id = forms.IntegerField(
        min_value=-9223372036854775808,
        max_value=9223372036854775807,
        label=_(f'4M Reference ID' ),
        label_suffix='',
        help_text=mark_safe('''NOTE:
            <ul>
                <li>The 4M form must be exist</li>
                <li>The 4M form must be approved by QA (not pending or rejected)</li>
                <li>The 4M form must be mapped to the location of the tool</li>
                <li>The 4M form had not used previously to boost the life of another tools</li>
            </ul>
        '''),
        widget=PrependedTextInput(
            attrs={'class': 'form-control',},
            prepend_text_list=[serve.xylem_code, serve.an_4m_digitalization],
            prepend_id_list=['prepend1','prepend2'],
        )
    )

    action_taken = forms.CharField(
        label=_('Action taken'),
        label_suffix='',
        widget = forms.Textarea(
            attrs = {
                'class' : 'form-control',
                "rows" : 3,
                "minlength" : action_taken_min_len,
                "maxlength": action_taken_max_len, 
            }
        ),
    )
    

    def __init__(self, *args, **kwargs):
        self.tps_map = kwargs.pop("tps_map")
        super().__init__(*args, **kwargs)


    def clean_four_m_form_ref_id(self):
        four_m_form_ref_id = self.cleaned_data.get('four_m_form_ref_id')
        try:
            four_m_form_ref = FourMFormModel.objects.get(id=four_m_form_ref_id)   
        except FourMFormModel.DoesNotExist:
            raise ValidationError(_("No 4M forms matches the given reference ID."))        
        if ToolHistoryLog.objects.filter(four_m_form_ref = four_m_form_ref).exists():
            raise ValidationError(_("Given 4M form was already used for boosting the life of another tool"))
        qa_appr_status = four_m_form_ref.a006_fma_fr.get(approval_needed_dept_i=serve.Depts.Inprocess_QA)
        if qa_appr_status.response is None:
            raise ValidationError(_("Given 4M form is pending for QA approval"))
        elif qa_appr_status.response is False:
            raise ValidationError(_("Given 4M form was rejected by QA"))
        pl = serve.get_production_line_of_ps(production_station = self.tps_map["tps_map"].production_station_i)
        if not FourMMapping.objects.filter(four_m_form_ref = four_m_form_ref, mapped_i = pl).exists():
            raise ValidationError(_(f"Given 4M form was not mapped for the {pl.name}"))
        return four_m_form_ref_id