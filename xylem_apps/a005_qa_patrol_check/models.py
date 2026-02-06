from django.db import models
from django.utils.translation import gettext_lazy as _


from xylem_apps.a000_xylem_master.models import UserProfile, PatrolCheckSheets
from xylem_apps.a000_xylem_master import serve 


class InspectionData(models.Model):
    patrol_checksheet = models.ForeignKey(PatrolCheckSheets, verbose_name=_('Patrol Checksheet'), on_delete=models.PROTECT, related_name='Inspection_data', db_constraint=False)
    inspec_datetime = models.DateTimeField(auto_now_add=True)

    for i in range(serve.qa_pcs_operator_input_elements_max):
        locals()[f'{serve.qa_pcs_operator_input_element_name}{i}'] = models.ForeignKey(UserProfile, verbose_name=_('Patrol Checksheet'), on_delete=models.PROTECT, related_name=f'patrol_operator{i}', db_constraint=False, null=True)

    for i in range(serve.qa_pcs_inspection_input_elements_max):
        locals()[f'{serve.qa_pcs_inspection_input_element_name}{i}'] = models.CharField(max_length=serve.qa_pcs_inspection_input_element_max_len, null=True)
    inspected_by = models.ForeignKey(UserProfile, verbose_name=_('Inspected by'), on_delete=models.PROTECT, related_name='id_inspected_by', db_constraint=False)
    response = models.BooleanField(null=True)
    responded_user = models.ForeignKey(UserProfile, verbose_name=_('Responded by'), on_delete=models.PROTECT, related_name='id_responded_by', db_constraint=False, null=True)
    response_datetime = models.DateTimeField(null=True)



class InspectionDataDuplet(models.Model):
    inspection_data_ref = models.OneToOneField(InspectionData, verbose_name=_('Inspection data reference'), on_delete=models.PROTECT, related_name='Inspection_data_duplet', primary_key=True, db_constraint=False)
    for i in range(serve.qa_pcs_inspection_input_elements_max):
        locals()[f'{serve.qa_pcs_inspection_input_element_name}{i}'] = models.CharField(
            max_length=serve.qa_pcs_inspection_input_element_max_len, null=True
        )
