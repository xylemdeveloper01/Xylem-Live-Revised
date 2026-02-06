from django import template

from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import UserProfile, PnDrawings, PnMTMapping


register = template.Library()
# @register.filter(name="get_production_line")
# def get_standard_date_format(value):
#   return get_production_line_of_ps(production_station=ps)


@register.filter(name="number_with_comma")
def number_with_comma(number):
	return serve.get_number_with_comma(number)


@register.filter(name="get_mail_prevented_status_of_user")
def get_mail_prevented_status_of_user(mail_icode, user_id):
	return serve.get_mail_prevented_status_of_user(mail_icode=mail_icode, user_id=user_id)


@register.filter(name="get_pc_id_of_item")
def get_pc_id_of_item(item):
	return serve.get_product_category_by_item(item=item).icode


@register.filter(name="get_pc_name_of_item")
def get_pc_name_of_item(item):
	return serve.get_product_category_by_item(item=item).name


@register.filter(name="get_name_of_icode")
def get_name_of_icode(icode):
	return serve.get_icode_object(icode).name


@register.filter(name="get_pl_name_of_ps")
def get_pl_name_of_ps(ps):
	return serve.get_production_line_of_ps(production_station=ps).name


@register.filter(name="get_pl_id_of_ps")
def get_pl_id_of_ps(ps):
	return serve.get_production_line_of_ps(production_station=ps).icode


@register.filter(name="get_pl_ps_name_of_ps")
def get_pl_ps_name_of_ps(ps):
	return serve.get_pl_ps_display_format(production_station=ps)


@register.filter(name="get_user_display_format")
def get_user_display_format(user = None, user_id = None):
	return serve.get_user_display_format(user = user, user_id = user_id)


@register.filter(name="get_tool_type_name_by_tool")
def get_tool_type_name_by_tool(tool = None, tool_id = None):
	return serve.get_tool_type_by_tool(tool = tool, tool_id = tool_id).name


@register.filter(name="icode_queryset_to_string")
def icode_queryset_to_string(queryset):
	return ', '.join(obj.name for obj in queryset)


@register.filter(name="get_access_to_del_py")
def get_access_to_del_py(user):
	profile = UserProfile.objects.get(id=user.id)
	if (profile.dept_i == serve.Depts.Inprocess_QA and profile.designation_i >= serve.Designations.Craftsman) or (profile.dept_i == serve.Depts.Development_team):
		return True 
	else :
		return False


@register.filter(name="get_pl_of_pn")
def get_pl_of_pn(part_number=None):
	production_lines = serve.get_production_lines_of_pn(part_number=part_number)
	return ", ".join([pl.name.strip() for pl in production_lines])


@register.simple_tag(name="get_xylem_manage_mail_footer_html")
def get_xylem_manage_mail_footer_html():
	return serve.get_xylem_manage_mail_footer_html()
	

@register.filter(name="get_draw_status_of_pn")
def get_draw_status_of_pn(part_number_i=None):
    return PnDrawings.objects.filter(part_number_i=part_number_i).exists()


@register.filter(name="get_model_of_pn")
def get_model_of_pn(part_number_i=None):
	if hasattr(part_number_i, "pn_pnmt_m"):
		return part_number_i.pn_pnmt_m.model_i.name
	return "-"


@register.filter(name="get_item")
def get_item(dictionary, key):
	return dictionary.get(key)