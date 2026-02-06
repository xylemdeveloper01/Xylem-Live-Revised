import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, UsernameField, PasswordResetForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from django.db.models import Max, Q
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.safestring import mark_safe

from . import serve
from .models import UserProfile, PcPlMapping, PnMTMapping, PnCpnMapping, PnPrlPsMapping, TPsMapping, PyPsMapping
pn_drawing_change_desc_min_len = 100
pn_drawing_change_desc_max_len = 500

class MaxFileSizeValidator:
    def __init__(self, max_size):
        self.max_size = max_size
        self.max_size_in_MB = int(max_size/(1024 * 1024))

    def __call__(self, value):
        file_size = value.size
        if file_size > self.max_size:
            raise ValidationError(_('File size exceeds the limit of %(max_size)s MB') % {'max_size': self.max_size_in_MB})
        

class IcodesModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class IcodesModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name
    

class PrependedTextInput(forms.Widget):
    def __init__(self, prepend_text_list, prepend_id_list, attrs = None):
        super().__init__(attrs)
        self.prepend_text_list = prepend_text_list
        self.prepend_id_list = prepend_id_list

    def render(self, name, value = '', attrs = None, renderer = None):
        input_html = forms.TextInput(attrs={'class': 'form-control'}).render(name, value, attrs)
        prepend_html = ''
        for id, text in zip(self.prepend_id_list, self.prepend_text_list):
            prepend_html = prepend_html + f'''<div class="input-group-prepend">
                <span class="input-group-text" id="{id}">{text}</span>
            </div>'''
        html = f'<div class="input-group">{prepend_html}{input_html}</div>'
        return mark_safe(html)


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label=_('First Name'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'autofocus': True}),
    )
    last_name = forms.CharField(
        label=_('Last Name'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
    )
    username = forms.CharField(
        label=_('Username / Employee ID'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username / Employee ID'}),
    )
    email = forms.CharField(
        label=_('Email ID'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email ID'}),
    )
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
    )
    gender_i = IcodesModelChoiceField(
        label = _('Select Gender'),
        queryset = serve.get_genders(),
        widget = forms.Select(attrs = {'class' : 'form-control'})
    )
    plant_location_i = IcodesModelChoiceField(
        label = _('Select Plant Location'),
        queryset=serve.get_plant_locations(),
        widget = forms.Select(attrs = {'class' : 'form-control'})
    )
    dept_i = IcodesModelChoiceField(
        label = _('Select Department'),
        queryset=serve.get_depts(),
        widget = forms.Select(attrs = {'class' : 'form-control'})
    )
    designation_i = IcodesModelChoiceField(
        label = _('Select Designation'),
        queryset=serve.get_designations(),
        widget = forms.Select(attrs = {'class' : 'form-control'})
    )    
    dob = forms.DateField(
        label = _('Date of Birth'),
        widget = forms.DateInput(attrs = {'class' : 'form-control', 'type' : 'date',}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dob'].widget.attrs.update(max=f"{datetime.datetime.now().date()-datetime.timedelta(days=16*365.25)}")

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'username', 'email', 'gender_i', 'plant_location_i', 'dept_i', 'designation_i', 'dob', 'password1', 'password2',)


class LoginForm(AuthenticationForm):
    error_messages = {  
        "inactive": _('Your approval is still pending with your IFS'),
        "deactivated" : _('Your Account is deactivated'),
        "invalid_login": _(
            "Please enter a correct username and password. Note that both "
            "fields may be case-sensitive."
        ),
    }
    username = UsernameField(label=_('Your Username'), widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username / Employee ID'}))
    password = forms.CharField(
        label=_('Your Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )
    def clean(self):            
        username = self.cleaned_data.get("username")        
        try:
            user = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            raise ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
            )        
        if user.is_active is None:
            raise ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )
        elif user.is_active is False:
            raise ValidationError(
                self.error_messages["deactivated"],
                code="deactivated",              
            )
        return super().clean()
    

class UserPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))


class UserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'New Password'
    }), label='New Password')
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm New Password'
    }), label='Confirm New Password')
    

class UserPasswordChangeForm(PasswordChangeForm):
    error_messages = {
        **PasswordChangeForm.error_messages,
        "password_old_new_same": _(
            "Your new password cannot be the old one. Please enter it again."
        ),
    }
    old_password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Old Password'
    }), label='Old Password')
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'New Password'
    }), label='New Password')
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm New Password'
    }), label='Confirm New Password')


    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        if self.user.check_password(password2):
            raise ValidationError(
                self.error_messages["password_old_new_same"],
                code="password_old_new_same",
            )
        password_validation.validate_password(password2, self.user)
        return password2
    

class EditUserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reg_form = RegistrationForm()
        self.temp_dict = {}   
        for key in ('first_name','last_name', 'username', 'email', 'gender_i', 'dob'):
            self.temp_dict[key] = self.reg_form.fields[key]   
        self.fields = self.temp_dict  

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name','username' ,'email', 'gender_i', 'dob')
        
    def clean(self):
        is_modified = False
        for field in self.fields:
            cleaned_value = super().clean().get(field) 
            initial_value = self.initial.get(field)
            # Handle ModelChoiceField specifically by comparing the primary key
            if isinstance(self.fields[field], forms.ModelChoiceField):        
                if cleaned_value is not None and cleaned_value.pk != initial_value:
                    is_modified = True
                    break
            else:             
                if cleaned_value != initial_value:
                    is_modified = True
                    break
        # If no fields were modified, raise a validation error
        if not is_modified:
            raise ValidationError(_('Hey dude, you should modify at least one field to update.'))
        return super().clean()
    

class ProductCategoryForm(forms.Form):
    error_messages = {  
        "product_category_exist": _("This product category is already exist"),
    }
    product_category_name = forms.CharField(
        label = _('Enter the product_category name'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the product category name', 'autofocus': True, }),
        help_text=_("Ex: Seat Belt, Height Adjuster, Driver Air Bag"),
    )

    def clean_product_category_name(self):
        """
        Validate that the product category is exist.
        """
        product_category_name = self.cleaned_data["product_category_name"]
        if serve.get_product_categories().filter(name=product_category_name).exists():
            raise ValidationError(
                self.error_messages["product_category_exist"],
                code="exist",
            )
        return product_category_name


class TechnologyCreationForm(forms.Form):
    error_messages = {  
        "technology_exist": _("This technology is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'autofocus': True, }),
    )
    technology_name = forms.CharField(
        label = _('Enter the technology name'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the technology name'}),
        help_text=_("Ex: SPR4.1, CAB"),
    )

    def clean_technology_name(self):
        """
        Validate that the technology is exist.
        """
        product_category = self.cleaned_data["product_category"]
        technology_name = self.cleaned_data["technology_name"]
        if serve.get_product_technologies(product_category).filter(name=technology_name).exists():
            raise ValidationError(
                self.error_messages["technology_exist"],
                code="exist",
            )
        return technology_name


class ProductionLineCreationForm(forms.Form):
    error_messages = {  
        "production_line_exist": _("This production line is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'autofocus': True, }),
    )
    production_line_name = forms.CharField(
        label = _('Enter the production line name'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the production line name'}),
        help_text=_("Ex: SPR4 BB, SPR4 3PGA1"),
    )

    def clean_production_line_name(self):
        """
        Validate that the production line is exist.
        """
        product_category = self.cleaned_data["product_category"]
        production_line_name = self.cleaned_data["production_line_name"]
        if serve.get_production_lines(product_category).filter(name=production_line_name).exists():
            raise ValidationError(
                self.error_messages["production_line_exist"],
                code="exist",
            )
        return production_line_name


class ProductionStationCreationForm(forms.Form):
    error_messages = {  
        "production_station_exist": _("This production station is already exist for the line"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'psc_id_product_category', 'autofocus': True, }),
    )
    production_line = IcodesModelChoiceField(
        label = _('Select the production line'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'psc_id_production_line'}),
    )
    production_station_name = forms.CharField(
        label = _('Enter the production station name'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the production station name'}),
        help_text=_("Ex: OP10: Roll Forming, SUB ASSY: DLL Cutter"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_category' in self.data:
            self.fields['production_line'].queryset = serve.get_production_lines(product_category_id=self.data.get('product_category'))

    def clean_production_station_name(self):
        """
        Validate that the production station is exist for the line.
        """
        production_line = self.cleaned_data["production_line"]
        production_station_name = self.cleaned_data["production_station_name"]
        if serve.get_production_stations(production_line).filter(name=production_station_name).exists():
            raise ValidationError(
                self.error_messages["production_station_exist"],
                code="exist",
            )
        return production_station_name
    

class ModelCreationForm(forms.Form):
    error_messages = {  
        "model_exist": _("This model is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'autofocus': True, }),
    )
    model_name = forms.CharField(
        label = _('Enter the model name'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the model name'}),
        help_text=_("Ex: W601, Q5 MCE"),
    )

    def clean_model_name(self):
        """
        Validate that the model is exist.
        """
        product_category = self.cleaned_data["product_category"]
        model_name = self.cleaned_data["model_name"]
        if serve.get_product_models(product_category).filter(name=model_name).exists():
            raise ValidationError(
                self.error_messages["model_exist"],
                code="exist",
            )
        return model_name


class PartNumberCreationForm(forms.Form):
    error_messages = {  
        "part_number_exist": _("This part number is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'autofocus': True, }),
    )
    # product_technology = IcodesModelChoiceField(
    #     label = _('Select the product\'s technology'),
    #     label_suffix = '',
    #     queryset = serve.get_icode_none_object(),
    #     widget = forms.Select(attrs={'class': 'form-control', 'id':'pnc_id_product_technology'}),
    # )
    # barcode_availablilty = IcodesModelChoiceField(
    #     label = _('Select the barcode availablilty'),
    #     label_suffix = '',
    #     queryset = serve.get_barcode_avl_types(),
    #     widget = forms.Select(attrs = { 'class' : 'form-control'}),
    # )
    part_number_name = forms.CharField(
        label = 'Enter the part number',
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the part number' }),
        help_text=_("Ex: 013 0127 00"),
    )
    part_number_desc = forms.CharField(
        label = 'Enter the part number\'s name',
        label_suffix = '',
        widget = forms.TextInput( attrs = { 'class' : 'form-control', 'placeholder' : 'type the part number\'s name' } ),
        help_text=_("Ex: 2 ROW 2PT LAP BELT ASSY"),
    )

    def clean_part_number_name(self):
        """
        Validate that the part number is exist.
        """
        product_category = self.cleaned_data["product_category"]
        part_number_name = self.cleaned_data["part_number_name"]
        if serve.get_part_numbers(product_category).filter(name=part_number_name).exists():
            raise ValidationError(
                self.error_messages["part_number_exist"],
                code="exist",
            )
        return part_number_name


class ChildPartNumberCreationForm(forms.Form):
    error_messages = {  
        "child_part_number_exist": _("This child part number is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'autofocus': True, }),
    )
    child_part_number_name = forms.CharField(
        label = _('Enter the child part number'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the child part number', }),
        help_text=_("Ex: 00 0987 00"),
    )
    child_part_number_desc = forms.CharField(
        label = 'Enter the child part number\'s name',
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the child part name' }),
        help_text=_("Ex: Spool"),
    )

    def clean_child_part_number_name(self):
        """
        Validate that the child part number is exist.
        """
        product_category = self.cleaned_data["product_category"]
        child_part_number_name = self.cleaned_data["child_part_number_name"]
        if serve.get_child_part_numbers(product_category).filter(name=child_part_number_name).exists():
            raise ValidationError(
                self.error_messages["child_part_number_exist"],
                code="exist",
            )
        return child_part_number_name


class RejectionReasonCreationForm(forms.Form): 
    error_messages = {  
        "rejection_reason_exist": _("This rejection reason is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'autofocus': True, }),
    )
    rejection_reason_name = forms.CharField(
        label = _('Enter the rejection reason name'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the rejection reason name'}),
        help_text=_("Ex: SB001: Metal noise"),
    )

    def clean_rejection_reason_name(self):
        """
        Validate that the rejection reason is exist.
        """
        product_category = self.cleaned_data["product_category"]
        rejection_reason_name = self.cleaned_data["rejection_reason_name"]
        if serve.get_rejection_reasons(product_category).filter(name=rejection_reason_name).exists():
            raise ValidationError(
                self.error_messages["rejection_reason_exist"],
                code="exist",
            )
        return rejection_reason_name


class ToolCreationForm(forms.Form):
    error_messages = {  
        "tool_exist": _("This tool is already exist for the product category"),
        "fixture_exist": _("This fixture is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset = serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'autofocus': True,}),
    )
    tool_type = IcodesModelChoiceField(
        label = _('Select tool type'),
        label_suffix = '',
        queryset = serve.get_tool_types(),
        widget = forms.Select(attrs = {'class': 'form-control', 'autofocus': True,}),
    )
    tool_name = forms.CharField(
        label = _('Enter the tool name'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the tool name'}),
        help_text = _("Ex: Snake punch tool"), 
    )
    
    def clean_tool_name(self):
        """
        Validate that the tool name is exist.
        """
        product_category = self.cleaned_data["product_category"]
        tool_type = self.cleaned_data["tool_type"]
        tool_name = self.cleaned_data["tool_name"]
        if  serve.get_tools( product_category=product_category, tool_type=tool_type).filter(name=tool_name).exists():
            if tool_type == serve.Others.tool_tools:
                raise ValidationError(
                    self.error_messages["tool_exist"],
                    code="exist",
                )
            raise ValidationError(
                self.error_messages["fixture_exist"],
                code="exist",
            ) 
        return tool_name
    
    
class PokaYokeCreationForm(forms.Form):
    error_messages = {  
        "poka_yoke_exist": _("This poka yoke already exist for the product category"),
    }

    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset = serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'autofocus': True,}),
    )

    poka_yoke_name = forms.CharField(
        label = _('Enter the poka yoke name'),
        label_suffix = '',
        widget = forms.TextInput(attrs = { 'class' : 'form-control', 'placeholder' : 'type the poka yoke name'}),
        help_text = _("Ex: ----------- "), 
    )
    
    def clean_poka_yoke_name(self):
        """
        Validate that the poka yoke is exist.
        """
        product_category = self.cleaned_data["product_category"]
        poka_yoke_name = self.cleaned_data["poka_yoke_name"]
        if serve.get_poka_yokes(product_category).filter(name=poka_yoke_name).exists():
            raise ValidationError(
                self.error_messages["poka_yoke_exist"],
                code="exist",
            )
        return poka_yoke_name


# Product Category - Plant Location Mapping Form
class PcPlMappingForm(forms.Form):
    error_messages = {  
        "mapping_exist": _("This type of mapping is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control'}),
    )
    plant_location = IcodesModelChoiceField(
        label = _('Select Plant Location'),
        label_suffix = '',
        queryset=serve.get_plant_locations(),
        widget = forms.Select(attrs = {'class' : 'form-control'})
    )
    def clean(self):
        """
        Validate that the mapping is exist.
        """
        super().clean()
        product_category = self.cleaned_data["product_category"]
        plant_location = self.cleaned_data["plant_location"]
        if PcPlMapping.objects.filter(product_category_i = product_category, plant_location_i = plant_location).exists():
            raise ValidationError(
                self.error_messages["mapping_exist"],
                code="exist",
            )


# Part Number - Model - Technology Mapping Form
class PnMTMappingForm(forms.Form):
    error_messages = {  
        "mapping_exist": _("This type of mapping is already exist for the product category"),
        "another_mapping_exist": _("This part number mapped already with another for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pnmt_id_product_category', 'autofocus': True, }),
    )
    part_number = IcodesModelChoiceField(
        label = _('Select Part Number'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pnmt_id_part_number', })
    )
    model = IcodesModelChoiceField(
        label = _('Select Model'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pnmt_id_product_model', })
    )
    technology = IcodesModelChoiceField(
        label = _('Select Technology'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pnmt_id_product_technology', })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_category' in self.data:
            self.fields['part_number'].queryset = serve.get_part_numbers(product_category_id=self.data.get('product_category'))
            self.fields['model'].queryset = serve.get_product_models(product_category_id=self.data.get('product_category'))
            self.fields['technology'].queryset = serve.get_product_technologies(product_category_id=self.data.get('product_category'))

    def clean(self):
        """
        Validate that the mapping is exist.
        """
        super().clean()
        part_number = self.cleaned_data["part_number"]
        model = self.cleaned_data["model"]
        technology = self.cleaned_data["technology"]
        if PnMTMapping.objects.filter(part_number_i = part_number, model_i = model, technology_i = technology).exists():
            raise ValidationError(
                self.error_messages["mapping_exist"],
                code="exist",
            )
        elif PnMTMapping.objects.filter(part_number_i = part_number).exists():
            raise ValidationError(
                self.error_messages["another_mapping_exist"],
                code="exist",
            )


# Part Number - Child Part Numbers Mapping Form
class PnCpnMappingForm(forms.Form):
    error_messages = {  
        "mapping_exist": _("This type of mapping is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pncpn_id_product_category', 'autofocus': True, }),
    )
    part_number = IcodesModelChoiceField(
        label = _('Select Part Number'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pncpn_id_part_number', })
    )
    child_part_numbers = IcodesModelMultipleChoiceField(
        label = _('Select Child Part Number'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.SelectMultiple(attrs = {'class' : 'form-control', 'id':'pncpn_id_child_part_number', })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_category' in self.data:
            self.fields['part_number'].queryset = serve.get_part_numbers(product_category_id=self.data.get('product_category'))
            self.fields['child_part_numbers'].queryset = serve.get_child_part_numbers(product_category_id=self.data.get('product_category'))

    def clean(self):
        """
        Validate that the mapping is exist.
        """
        super().clean()
        part_number = self.cleaned_data["part_number"]
        child_part_numbers = self.cleaned_data["child_part_numbers"]
        for child_part_number in child_part_numbers:
            if PnCpnMapping.objects.filter(part_number_i = part_number, child_part_number_i = child_part_number).exists():
                raise ValidationError(
                    self.error_messages["mapping_exist"]+f"( {part_number.name} {child_part_number.name})",
                    code="exist",
                )


# Part Number - Production line & Stations Mapping Form
class PnPrlPsMappingForm(forms.Form):
    error_messages = {  
        "mapping_exist": _("This type of mapping is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pnprlps_id_product_category', 'autofocus': True, }),
    )
    part_number = IcodesModelChoiceField(
        label = _('Select Part Number'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pnprlps_id_part_number', })
    )
    production_line = IcodesModelChoiceField(
        label = _('Select Production Line '),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'pnprlps_id_production_line', })
    )
    production_stations = IcodesModelMultipleChoiceField(
        label = _('Select Production Stations '),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.SelectMultiple(attrs = {'class' : 'form-control', 'id':'pnprlps_id_production_stations', })
    )
    cycle_time = forms.IntegerField(
        label = _('Enter the cycle time in seconds'),
        label_suffix = '',
        widget = forms.NumberInput(attrs = { 'class' : 'form-control', 'min':1 }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_category' in self.data:
            self.fields['part_number'].queryset = serve.get_part_numbers(product_category_id=self.data.get('product_category'))
            self.fields['production_line'].queryset = serve.get_production_lines(product_category_id=self.data.get('product_category'))
            self.fields['production_stations'].queryset = serve.get_production_stations(production_line_id=self.data.get('production_line'))
    
    def clean(self):
        """
        Validate that the mapping is exist.
        """
        super().clean()
        part_number = self.cleaned_data["part_number"]
        production_line = self.cleaned_data["production_line"]
        production_stations = self.cleaned_data["production_stations"]
        for production_station in production_stations:
            if PnPrlPsMapping.objects.filter(part_number_i = part_number, production_line_i = production_line, production_station_i = production_station).exists():
                raise ValidationError(
                    self.error_messages["mapping_exist"]+f"( {part_number.name} {production_line.name} {production_station.name})",
                    code="exist",
                )


# Tool - Production Station Mapping Form
class TPsMappingForm(forms.Form):
    error_messages = {  
        "mapping_exist": _("This type of mapping is already exist for the product category"),
        "value_overflow": _(f"Tool's low life consideration should be {serve.low_life_consideration_thresold_start_percent_from_full_life}% - {serve.low_life_consideration_thresold_end_percent_from_full_life}% to the tool's full life"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'tps_id_product_category', 'autofocus': True, }),
    )
    tool_type = IcodesModelChoiceField(
        label = _('Select tool type'),
        label_suffix = '',
        queryset = serve.get_tool_types(),
        widget = forms.Select(attrs = {'class': 'form-control', 'id': 'tps_tool_type',}),
    )
    tool = IcodesModelChoiceField(
        label = _('Select tool'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'tps_id_tool',})
    )
    production_line = IcodesModelChoiceField(
        label = _('Select Production Line'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'tps_id_production_line',})
    )
    production_station = IcodesModelChoiceField(
        label = _('Select Production Station'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'tps_id_production_station',})
    )
    parts_freq = forms.IntegerField(
        label = _('Parts frequency while production'),
        label_suffix = '',
        widget = forms.NumberInput(attrs = { 'class' : 'form-control', 'min':1, 'max': 10, 'value':1, 'id':'tps_id_parts_freq',}),
    )
    full_life = forms.IntegerField(
        label = _('Enter the tool\'s full life count'),
        label_suffix = '',
        widget = forms.NumberInput(attrs = { 'class' : 'form-control', 'min':1 }),
    )
    low_life_consideration = forms.IntegerField(
        label = _('Low life consideration point (below this point, tool will be consider to be of low life)'),
        label_suffix = '',
        help_text = _(f"Note: Allowed range {serve.low_life_consideration_thresold_start_percent_from_full_life}% - {serve.low_life_consideration_thresold_end_percent_from_full_life}% to the tool's full life"),
        widget = forms.NumberInput(attrs = { 'class' : 'form-control', 'min':1 }),
    )
    tool_image = forms.ImageField(
        label = _('Upload image of the tool'),
        label_suffix = '',
        help_text='Note : Allowed formats - JPG, JPEG, PNG. Maximum file size - 5MB',
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif']), 
            MaxFileSizeValidator(5 * 1024 * 1024)  # 5 MB in bytes
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_category' in self.data:
            self.fields['tool'].queryset = serve.get_icode_objects([self.data.get('tool')])
            self.fields['production_line'].queryset = serve.get_icode_objects([self.data.get('production_line')])
            self.fields['production_station'].queryset = serve.get_icode_objects([self.data.get('production_station')])
            tool_type = int(self.data.get('tool_type'))
            if tool_type == serve.Others.tool_fixtures.icode:
                self.fields['parts_freq'].required = True
            else:
                self.fields['parts_freq'].required = False
    
    def clean(self):
        """
        Validate that the mapping is exist.
        """
        super().clean()
        tool = self.cleaned_data["tool"]
        production_station = self.cleaned_data["production_station"]
        if TPsMapping.objects.filter(tool_i = tool, production_station_i = production_station).exists():
            raise ValidationError(
                self.error_messages["mapping_exist"],
                code="exist",
            )
    
    
    def clean_low_life_consideration(self):
        """
        Validate that the tool life and low_life_consideration.
        """
        full_life = self.cleaned_data["full_life"]
        low_life_consideration = self.cleaned_data["low_life_consideration"]
        if not (low_life_consideration >=  (serve.low_life_consideration_thresold_start_percent_from_full_life/100)*(full_life) and\
            low_life_consideration <=  (serve.low_life_consideration_thresold_end_percent_from_full_life/100)*(full_life)):
            raise ValidationError(
                self.error_messages["value_overflow"],
                code="value_overflow",
            )
        return low_life_consideration


# Poka Yoke - Production Station Mapping Form
class PyPsMappingForm(forms.Form):
    error_messages = {  
        "mapping_exist": _("This type of mapping is already exist for the product category"),
    }
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'pyps_id_product_category', 'autofocus': True, }),
    )
    poka_yoke = IcodesModelChoiceField(
        label = _('Select Poka Yoke'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'pyps_id_poka_yoke',})
    )
    production_line = IcodesModelChoiceField(
        label = _('Select Production Line '),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'pyps_id_production_line', })
    )
    production_station = IcodesModelChoiceField(
        label = _('Select Production Station'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'pyps_id_production_station',})
    )
    criticality_level = IcodesModelChoiceField(
        label = _('Select Criticality Level'),
        label_suffix = '',
        queryset=serve.get_poka_yoke_criticality_levels(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'pyps_id_criticality_level',})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_category' in self.data:
            self.fields['poka_yoke'].queryset = serve.get_icode_objects([self.data.get('poka_yoke')])
            self.fields['production_line'].queryset = serve.get_icode_objects([self.data.get('production_line')])
            self.fields['production_station'].queryset = serve.get_icode_objects([self.data.get('production_station')])

    def clean(self):
        """
        Validate that the mapping is exist.
        """
        super().clean()
        poka_yoke = self.cleaned_data["poka_yoke"]
        production_station = self.cleaned_data["production_station"]
        if PyPsMapping.objects.filter(poka_yoke_i = poka_yoke, production_station_i = production_station).exists():
            raise ValidationError(
                self.error_messages["mapping_exist"],
                code="exist",
            )


class PlMPnSelectionForm(forms.Form):
    product_category = IcodesModelChoiceField(
        label = _('Select the Product Category'),
        label_suffix = '',
        queryset=serve.get_product_categories(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'plmpn_id_product_category', 'autofocus': True, }),
    )
    production_line = IcodesModelChoiceField(
        label = _('Select Production Line '),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select(attrs = {'class' : 'form-control', 'id':'plmpn_id_production_line', })
    )
    model = IcodesModelChoiceField(
        label = _('Select Model'),
        label_suffix = '',
        queryset=serve.get_icode_none_object(),
        widget = forms.Select( attrs = { 'class' : 'form-control', 'id':'plmpn_id_product_model', })
    )
    part_number = IcodesModelChoiceField(
        label = _('Select Part Number'),
        label_suffix = '',
        queryset = serve.get_icode_none_object(),
        widget = forms.Select(attrs = { 'class' : 'form-control', 'id':'plmpn_id_part_number', })
    )
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'product_category' in self.data:
            self.fields['production_line'].queryset = serve.get_production_lines(product_category_id=self.data.get('product_category'))
            self.fields['model'].queryset = serve.get_product_models_of_pl(production_line_id=self.data.get('production_line'))
            self.fields['part_number'].queryset = serve.get_part_numbers_of_pl(production_line_id=self.data.get('production_line'))


class ToolLifeParamEditForm(forms.ModelForm, TPsMappingForm): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_dict = {}   
        for key in ('full_life','low_life_consideration', 'parts_freq'):
            self.temp_dict[key] = self.fields[key]   
        self.fields = self.temp_dict   

    def clean(self):
        is_modified = False
        for field in self.fields:
            cleaned_value = super().clean().get(field) 
            initial_value = self.initial.get(field)
            # Handle ModelChoiceField specifically by comparing the primary key
            if isinstance(self.fields[field], forms.ModelChoiceField):        
                if cleaned_value is not None and cleaned_value.pk != initial_value:
                    is_modified = True
                    break
            else:             
                if cleaned_value != initial_value:
                    is_modified = True
                    break
        # If no fields were modified, raise a validation error
        if not is_modified:
            raise ValidationError(_('Hey dude, you should modify at least one field to update.'))
        return super().clean()

    class Meta:
        model = TPsMapping
        fields = ('full_life','low_life_consideration', 'parts_freq')


class ToolPartNumberMapEditForm(forms.Form): 
    part_numbers = IcodesModelMultipleChoiceField(
        label=_('Select part Numbers'),
        label_suffix='',
        queryset=serve.get_icode_none_object(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}) 
    )
    
    def __init__(self, *args, **kwargs):
        self.pns = kwargs.pop('pns')
        super().__init__(*args, **kwargs)        
        self.fields['part_numbers'].queryset = self.pns


class ToolImageEditForm(forms.ModelForm, TPsMappingForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)       
        self.temp_dict = {}   
        for key in ('tool_image',):
            self.temp_dict[key] = self.fields[key]   
        self.fields = self.temp_dict    
        self.fields['tool_image'].widget.attrs = {"accept":"image/*", "required": "True"}

    class Meta:
        model = TPsMapping
        fields = ('tool_image',)


class OEEEventsForm(forms.Form):
    oee_event = IcodesModelChoiceField(
        label = _('Select the oee event to map'),
        label_suffix = '',
        queryset = serve.get_oee_events(),
        widget = forms.Select( attrs = { 'class' : 'form-control', 'autofocus': True, })
    )


class PnDrawingForm(forms.Form):
    change_desc = forms.CharField(
        label = 'Details of drawing description',
        label_suffix = '',
        widget = forms.Textarea(attrs = { 'class' : 'form-control',  'id':'fm_form_id_chage_desc', "rows":3,
            "minlength":pn_drawing_change_desc_min_len, "maxlength": pn_drawing_change_desc_max_len, }),
    )
    drawing_file = forms.FileField(
        label = _('Upload drawing of the Partnumber'),
        label_suffix = '',
        help_text='Note : Allowed format - pdf. Maximum file size - 30MB',
        validators=[
            FileExtensionValidator(['pdf']),
            MaxFileSizeValidator(30 * 1024 * 1024)  # 30 MB in bytes
        ]
    )

