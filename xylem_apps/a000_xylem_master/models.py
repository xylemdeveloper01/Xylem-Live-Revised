import datetime
from django.db import models
from django.db.models import Q, F, Sum, Max
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

pn_drawing_change_desc_max_len = 500

class Icodes(models.Model):
    icode = models.PositiveIntegerField(primary_key = True)
    name = models.CharField(max_length = 100)
    description = models.CharField(max_length = 100, null=True)
    last_edited = models.DateTimeField(auto_now = True)


class UserProfile(AbstractUser):
    gender_i = models.ForeignKey(Icodes, verbose_name=_('Gender'), on_delete=models.PROTECT, related_name='gender')
    plant_location_i = models.ForeignKey(Icodes, verbose_name=_('Plant Location'), on_delete=models.PROTECT, related_name='plant_location')
    dept_i = models.ForeignKey(Icodes, verbose_name=_('Department'), on_delete=models.PROTECT, related_name='dept')
    designation_i = models.ForeignKey(Icodes, verbose_name=_('Designation'), on_delete=models.PROTECT, related_name ='designation')
    dob = models.DateField(_('Date of Birth'))
    is_active = models.BooleanField(
        _("active"),
        null=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    responded_by = models.ForeignKey("self", verbose_name=_('Approved by'), on_delete=models.PROTECT, related_name='approved_by', null=True)

    def _str_(self):
        return self.name


class UserExtraFields(models.Model):
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    extra1 = models.BooleanField(default=False)
    extra2 = models.BigIntegerField(null=True)


class MailDepartmentMapping(models.Model):
    mail_i = models.ForeignKey(Icodes, verbose_name=_('Mail'), on_delete=models.PROTECT, related_name='mdm_m')
    dept = models.ForeignKey(Icodes, verbose_name=_('User'), on_delete=models.PROTECT, related_name='mdm_d')


class MailUserMapping(models.Model):
    mail_i = models.ForeignKey(Icodes, verbose_name=_('Mail'), on_delete=models.PROTECT, related_name='mum_m')
    user = models.ForeignKey(UserProfile, verbose_name=_('User'), on_delete=models.PROTECT, related_name='mum_u')


class MailExternalmailidsMapping(models.Model):
    mail_i = models.ForeignKey(Icodes, verbose_name=_('Mail'), on_delete=models.PROTECT, related_name='mem_m')
    external_mail_id = models.EmailField(verbose_name=_('External Mail ID'))


class UserPreventedMails(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name=_('User'), on_delete=models.PROTECT, related_name='upm_u')
    mail_i = models.ForeignKey(Icodes, verbose_name=_('Mail'), on_delete=models.PROTECT, related_name='upm_m', db_column='mail_code')


# Product Category - Plant Location Mapping Model
class PcPlMapping(models.Model):
    product_category_i = models.ForeignKey(Icodes, verbose_name=_('Product Category'), on_delete=models.PROTECT, related_name='pc_pcpl_m')
    plant_location_i = models.ForeignKey(Icodes, verbose_name=_('Product Location'), on_delete=models.PROTECT, related_name='pl_pcpl_m')
    datetime_mapped = models.DateTimeField(auto_now=True)
    mapped_by = models.ForeignKey(UserProfile, verbose_name=_('Mapped by'), on_delete=models.PROTECT, related_name='pcpl_mapped_by')


# Part Number - Model - Technology Mapping Model
class PnMTMapping(models.Model):
    part_number_i = models.OneToOneField(Icodes, verbose_name=_('Part Number Category'), on_delete=models.PROTECT, related_name='pn_pnmt_m', primary_key=True)
    model_i = models.ForeignKey(Icodes, verbose_name=_('Model'), on_delete=models.PROTECT, related_name='m_pnmt_m')
    technology_i = models.ForeignKey(Icodes, verbose_name=_('Technology'), on_delete=models.PROTECT, related_name='t_pnmt_m')
    datetime_mapped = models.DateTimeField(auto_now=True)
    mapped_by = models.ForeignKey(UserProfile, verbose_name=_('Mapped by'), on_delete=models.PROTECT, related_name='pnmt_mapped_by')


# Part Number - Child Part Numbers Mapping Model
class PnCpnMapping(models.Model):
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='pc_pncpn_m')
    child_part_number_i = models.ForeignKey(Icodes, verbose_name=_('Child Part Number'), on_delete=models.PROTECT, related_name='cpn_pncpn_m')
    datetime_mapped = models.DateTimeField(auto_now=True)
    mapped_by = models.ForeignKey(UserProfile, verbose_name=_('Mapped by'), on_delete=models.PROTECT, related_name='pncpn_mapped_by')


# Part Number - Production line & Station Mapping Model
class PnPrlPsMapping(models.Model):
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='pn_pnprlps_m')
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='prl_pnprlps_m')
    production_station_i = models.ForeignKey(Icodes, verbose_name=_('Production Station'), on_delete=models.PROTECT, related_name='ps_pnprlps_m')
    datetime_mapped = models.DateTimeField(auto_now=True)
    mapped_by = models.ForeignKey(UserProfile, verbose_name=_('Mapped by'), on_delete=models.PROTECT, related_name='pnplps_mapped_by')


# Part Number - Production line & cycle time
class PnPrlCtData(models.Model):
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='pn_pnprlct')
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='prl_pnprlct')
    cycle_time = models.PositiveSmallIntegerField(verbose_name=_('Cycle time in seconds'))
    last_edited = models.DateTimeField(auto_now=True)
    edited_by = models.ForeignKey(UserProfile, verbose_name=_('Edited by'), on_delete=models.PROTECT, related_name='pnprlct_edited_by')


# Tool - Production Station Mapping Model
class TPsMapping(models.Model):
    tool_i = models.ForeignKey(Icodes, verbose_name=_('Tool'), on_delete=models.PROTECT, related_name='t_tps_m')
    production_station_i = models.ForeignKey(Icodes, verbose_name=_('Production Station'), on_delete=models.PROTECT, related_name='ps_tps_m')
    full_life = models.PositiveIntegerField(verbose_name=_('Tool\'s Full Life'))
    low_life_consideration = models.PositiveIntegerField(verbose_name=_('Tool\'s Low Life Consideration start from'))
    parts_freq = models.PositiveSmallIntegerField(null=True)
    tool_image = models.ImageField(verbose_name=_('Image of the tool'), upload_to='a000/tool_images/')
    datetime_mapped = models.DateTimeField(auto_now_add=True)
    mapped_by = models.ForeignKey(UserProfile, verbose_name=_('Mapped by'), on_delete=models.PROTECT, related_name='tps_mapped_by')


# Tool , Production Station Map - Part Number Excluded Mapping Model
class TPsmapPnExMapping(models.Model):
    tps_map = models.ForeignKey(TPsMapping, verbose_name=_('Tps map Form Reference'), on_delete=models.PROTECT, related_name='t_tpspn_m')
    part_number_i =  models.ForeignKey(Icodes, verbose_name=_('Part Number'),on_delete=models.PROTECT, related_name='pn_tpspn_m',db_constraint=False)


# Poka Yoke - Production Station Mapping Model
class PyPsMapping(models.Model):
    poka_yoke_i = models.ForeignKey(Icodes, verbose_name=_('Poka Yoke'), on_delete=models.PROTECT, related_name='py_pyps_m')
    production_station_i = models.ForeignKey(Icodes, verbose_name=_('Production Station'), on_delete=models.PROTECT, related_name='ps_pyps_m')
    criticality_level = models.ForeignKey(Icodes, verbose_name=_('Criticality Level'), on_delete=models.PROTECT, related_name='cl_pyps_m')
    datetime_mapped = models.DateTimeField(auto_now_add=True)
    mapped_by = models.ForeignKey(UserProfile, verbose_name=_('Mapped by'), on_delete=models.PROTECT, related_name='pyps_mapped_by')

    @property
    def upcoming_due_date(self): # next inspection's due date
        inspection_due_date__max =  self.a010_pi_pm.all().aggregate(Max("inspection_due_date"))["inspection_due_date__max"]
        today_date = datetime.datetime.now().date()
        if inspection_due_date__max:
            due_date = inspection_due_date__max
            if inspection_due_date__max<=today_date:
                due_date = due_date + datetime.timedelta(days=int(self.criticality_level.description))
        else:
            due_date = self.datetime_mapped.date() + datetime.timedelta(days=int(self.criticality_level.description))
        return due_date


# OEE Event - Department Mapping Model
class OeDMapping(models.Model):
    what_id = models.OneToOneField(Icodes, verbose_name='What_id', on_delete=models.PROTECT, related_name='wi_oed_m', primary_key=True)
    mapped_user = models.ForeignKey(UserProfile, verbose_name=_('Mapped by'), on_delete=models.PROTECT, related_name='mu_oed_m')
    dept_i = models.ForeignKey(Icodes, verbose_name='Department', on_delete=models.PROTECT, related_name='d_oed_m')
    last_modified = models.DateTimeField(auto_now=True)


class PatrolCheckSheets(models.Model):
    production_line_i = models.ForeignKey(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='pl_pcs')
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='pn_pcs')
    cs_version = models.PositiveSmallIntegerField()
    created_by = models.ForeignKey(UserProfile, verbose_name=_('Created by'), on_delete=models.PROTECT, related_name='pcs_created_by')
    checksheet_html = models.TextField()
    alive_flag = models.BooleanField()
    date_time = models.DateTimeField(auto_now=True)
    deactivated_by = models.ForeignKey(UserProfile, verbose_name=_('Deactivated by'), on_delete=models.PROTECT, related_name='pcs_deactivated_by', null=True)


class SocketWhereIDs(models.Model):
    where_id = models.OneToOneField(Icodes, verbose_name=_('where ID'), on_delete=models.PROTECT, related_name='swi_wi', primary_key=True)
    ma_trig_delay = models.PositiveSmallIntegerField(verbose_name=_('Trigger delay for maintenance alert in seconds'))


class DataPanelActivity(models.Model):
    relevant_user = models.ForeignKey(UserProfile, verbose_name=_('Relevant User'), on_delete=models.PROTECT, related_name='ru_dpa')
    model_name = models.CharField(max_length=50)
    model_object_id = models.PositiveIntegerField()
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now=True)


class OEEProductionLineSetting(models.Model):
    production_line_i = models.OneToOneField(Icodes, verbose_name=_('Production Line'), on_delete=models.PROTECT, related_name='opls_pl', primary_key=True)
    production_station_i = models.OneToOneField(Icodes, verbose_name=_('Production Station used for OEE calculation'), on_delete=models.PROTECT, related_name='opls_ps')
    default_ct = models.PositiveSmallIntegerField(verbose_name=_('default cycle time of Production Line in seconds (higher cycle time among running parts)'))
    ie_min_to_reg_m = models.PositiveSmallIntegerField(verbose_name=_('Minimum time to register idle event in minutes'))
    ie_l1_es_m = models.PositiveSmallIntegerField(verbose_name=_('Idle event Level1 escalation minutes'))
    ie_l2_es_m = models.PositiveSmallIntegerField(verbose_name=_('Idle event Level2 escalation minutes'))
    ie_l3_es_m = models.PositiveSmallIntegerField(verbose_name=_('Idle event Level3 escalation minutes'))
    dashboard_ht = models.PositiveSmallIntegerField(verbose_name=_('OEE Dashboard holding time for the production line in milliseconds'))
    pl_grp_cl_bg = models.CharField(verbose_name=_('Production Line Grouping Backgroud Color as HTML code'), max_length=7)
    pl_grp_cl_txt = models.CharField(verbose_name=_('Production Line Text Color for the better visibility in background color as HTML code'), max_length=7)
    last_edited_by = models.ForeignKey(UserProfile, verbose_name=_('Last edited by'), on_delete=models.PROTECT, related_name='opls_le_by')


class UnsentMails(models.Model):
    subject = models.CharField(max_length=255)
    text_content = models.TextField(null=True)
    html_content = models.TextField(null=True)
    to_list = models.TextField()
    cc_list = models.TextField(null=True)
    bcc_list = models.TextField(null=True)
    status = models.BooleanField(default=False)
    attachments_path_list = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WorkflowForms(models.Model):
    form_name = models.CharField(max_length=255)
    fs_version = models.PositiveSmallIntegerField()
    status_flag = models.PositiveSmallIntegerField()
    date_time = models.DateTimeField(auto_now=True)
    action_description = models.CharField(max_length=100, null=True) 
    created_by = models.ForeignKey(UserProfile, verbose_name=_('Created by'), on_delete=models.PROTECT, related_name='wf_cb')


class WorkflowFormSections(models.Model):
    form_name = models.ForeignKey(WorkflowForms, verbose_name='_(Forms Name)', on_delete=models.CASCADE, related_name='fm_nm')
    section_name = models.CharField(max_length=200) 
    section_order = models.IntegerField() 
    section_html = models.TextField()


class workflowSectionDepartmentMapping(models.Model):
    section = models.ForeignKey(WorkflowFormSections, on_delete=models.PROTECT, related_name='mapping_sections',db_constraint=False) 
    assigned_department = models.ForeignKey(Icodes,verbose_name=_("assigned_department"),on_delete=models.PROTECT,related_name="as_dp",null=True,db_constraint=False)


class WorkflowFormApprover(models.Model):
    approver_order = models.IntegerField() 
    form = models.ForeignKey(WorkflowForms, on_delete=models.PROTECT,db_constraint=False)
    user_dept = models.ForeignKey(Icodes,verbose_name=_("user_department"),on_delete=models.PROTECT,related_name="app_usr_dep",null=True,db_constraint=False)
    dept_based_user = models.ForeignKey(Icodes,verbose_name=_("departmnet"),on_delete=models.PROTECT,related_name="app_dep",null=True,db_constraint=False)
    user = models.ForeignKey(UserProfile,verbose_name=_("user"), on_delete=models.PROTECT,related_name="app_usr",null=True)
    daywise = models.PositiveIntegerField(null=True)      
    weekly_day = models.CharField(max_length=100, null=True) 
    alert_name = models.CharField(max_length=100, null=True) 
    monthly_day = models.PositiveIntegerField(null=True)  
    auto_approve_days = models.PositiveIntegerField(null=True)  
    time = models.TimeField(null=True) 
    auto_approve = models.BooleanField(default=False)


class WorkflowApproverMapping(models.Model):
    form_section = models.ForeignKey(WorkflowFormSections, on_delete=models.PROTECT,related_name="mapping_form",null=True,db_constraint=False)
    approver_section = models.ForeignKey(WorkflowFormApprover, on_delete=models.PROTECT,related_name="mapping_approver",null=True,db_constraint=False)
    approver_level = models.PositiveIntegerField(null=True)  
    parallel_order = models.PositiveIntegerField(null=True)


class PnDrawings(models.Model):
    part_number_i = models.ForeignKey(Icodes, verbose_name=_('Part Number'), on_delete=models.PROTECT, related_name='pd_pn')
    drawing_file = models.FileField(upload_to ='a000/part_drawings/')
    version = models.PositiveSmallIntegerField(verbose_name=_('Latest Drawing for this partnumber'))
    added_user = models.ForeignKey(UserProfile, verbose_name=_('Last edited by'), on_delete=models.PROTECT, related_name='pd_au')
    change_desc = models.CharField(max_length=pn_drawing_change_desc_max_len)
    created_at = models.DateTimeField(auto_now_add=True)