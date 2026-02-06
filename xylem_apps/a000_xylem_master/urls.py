from django.urls import path
from xylem_apps.a000_xylem_master import views
from django.contrib.auth import views as auth_views

urlpatterns = [

  # Components  
  path('components/button/', views.bc_button, name='bc_button'),
  path('components/badges/', views.bc_badges, name='bc_badges'),
  path('components/breadcrumb-pagination/', views.bc_breadcrumb_pagination, name='bc_breadcrumb_pagination'),
  path('components/collapse/', views.bc_collapse, name='bc_collapse'),
  path('components/tabs/', views.bc_tabs, name='bc_tabs'),
  path('components/typography/', views.bc_typography, name='bc_typography'),
  path('components/feather-icon/', views.icon_feather, name='icon_feather'),

  # Forms and Tables
  path('forms/form-elements/', views.form_elements, name='form_elements'),
  path('tables/basic-tables/', views.basic_tables, name='basic_tables'),

  # Chart and Maps
  path('charts/morris-chart/', views.morris_chart, name='morris_chart'),
  path('maps/google-maps/', views.google_maps, name='google_maps'),

  # Authentication
  path('accounts/register/', views.UserRegistrationView.as_view(), name='register'),
  path('accounts/login/', views.UserLoginView.as_view(), name='login'),
  path('accounts/logout/', views.logout_view, name='logout'),

  path('accounts/password-change/', views.UserPasswordChangeView.as_view(), name='password_change'),
  path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(
      template_name='accounts/auth-password-change-done.html'
  ), name="password_change_done"),

  path('accounts/password-reset/', views.UserPasswordResetView.as_view(), name='password_reset'),
  path('accounts/password-reset-confirm/<uidb64>/<token>/',
    views.UserPasswrodResetConfirmView.as_view(), name="password_reset_confirm"
  ),
  path('accounts/password-reset-done/', auth_views.PasswordResetDoneView.as_view(
    template_name='accounts/auth-password-reset-done.html'
  ), name='password_reset_done'),
  path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
    template_name='accounts/auth-password-reset-complete.html'
  ), name='password_reset_complete'),

  # Other URLs
  path('profile/', views.profile, name='profile'),
  path('profile/edit/<int:user_id>/', views.edit_user_profile_view, name='edit_user_profile'),
  path('manage_mails/', views.manage_mails, name='manage_mails'),

  path('sample-page/', views.sample_page, name='sample_page'),
  path('approvals/new_users_handle/<int:current_pagination_option_id>/<int:current_page_num>/', views.new_users_handle, name='new_users_handle'),
  path('dept_org_chart/<int:dept_id>/', views.dept_org_chart, name='dept_org_chart'),

  path('data-panel/part/<int:current_product_category_id>/', views.dp_part, name='dp_part'),

  path('data-panel/qa_patrol/<int:current_product_category_id>/<int:current_checksheet_status_type_id>/', views.dp_qa_patrol, name='dp_qa_patrol'),
  path('data-panel/qa_patrol/cs_selection/<int:current_product_category_id>/addition/', views.qa_patrol_cs_selection_add, name='qa_patrol_cs_selection_add'),
  path('data-panel/qa_patrol/cs_addition/<int:production_line_id>/<int:part_number_id>/', views.qa_patrol_cs_addition, name='qa_patrol_cs_addition'),
  path('data-panel/qa_patrol/cs_addition/upload', views.fetch_qa_pcs_addition_upload, name='fetch_qa_pcs_addition_upload'),
  path('data-panel/qa_patrol/cs_addition/<int:production_line_id>/<int:part_number_id>/save/', views.fetch_qa_patrol_cs_save, name='fetch_qa_patrol_cs_save'),
  path('data-panel/qa_patrol/cs_modification/<int:qa_pcs_id>/', views.qa_patrol_cs_modification, name='qa_patrol_cs_modification'),
  path('data-panel/qa_patrol/cs_view/<int:qa_pcs_id>/', views.qa_patrol_cs_view, name='qa_patrol_cs_view'),
  path('data-panel/qa_patrol/cs_deactivate/<int:qa_pcs_id>/', views.qa_patrol_cs_deactivate, name='qa_patrol_cs_deactivate'),

  path('data-panel/pn_drawings/<int:current_product_category_id>/<int:current_part_drawing_status_id>/<int:current_pagination_option_id>/<int:current_page_num>/', views.dp_pn_drawings, name='dp_pn_drawings'),
  path('data-panel/pn_drawings/add_pn_drawings/<int:part_number_id>/', views.add_pn_drawings, name='add_pn_drawings'),
  path('data-panel/pn_drawings/update_pn_drawings/<int:part_number_id>/', views.update_pn_drawings, name='update_pn_drawings'),
  path('data-panel/pn_drawings/view_pn_drawings/<int:part_number_id>/', views.view_pn_drawings, name='view_pn_drawings'),

  path('data-panel/workflows/<int:current_workflow_status_type_id>/', views.dp_workflows, name='dp_workflows'),
  path('data-panel/workflows/form_addition/', views.wf_form_addition, name='wf_form_addition'),
  path('data-panel/workflows/form_save/', views.dp_wf_form_save, name='dp_wf_form_save'),

  path('data-panel/product_category_addition/<int:current_product_category_id>/', views.product_category_addition, name='product_category_addition'),
  path('data-panel/tech_addition/<int:current_product_category_id>/', views.tech_addition, name='tech_addition'),
  path('data-panel/prod_line_addition/<int:current_product_category_id>/', views.prod_line_addition, name='prod_line_addition'),
  path('data-panel/prod_station_addition/<int:current_product_category_id>/', views.prod_station_addition, name='prod_station_addition'),
  path('data-panel/model_addition/<int:current_product_category_id>/', views.model_addition, name='model_addition'),
  path('data-panel/part_number_addition/<int:current_product_category_id>/', views.part_number_addition, name='part_number_addition'),
  path('data-panel/cp_number_addition/<int:current_product_category_id>/', views.cp_number_addition, name='cp_number_addition'),
  path('data-panel/rejection_reason_addition/<int:current_product_category_id>/', views.rejection_reason_addition, name='rejection_reason_addition'),
  path('data-panel/tool_addition/<int:current_product_category_id>/', views.tool_addition, name='tool_addition'),
  path('data-panel/poka_yoke_addition/<int:current_product_category_id>/', views.poka_yoke_addition, name='poka_yoke_addition'),

  path('data-panel/pcpl_mapping/<int:current_product_category_id>/', views.pcpl_mapping, name='pcpl_mapping'),
  path('data-panel/pnmt_mapping/<int:current_product_category_id>/', views.pnmt_mapping, name='pnmt_mapping'),
  path('data-panel/pncpn_mapping/<int:current_product_category_id>/', views.pncpn_mapping, name='pncpn_mapping'),
  path('data-panel/pnprlps_mapping/<int:current_product_category_id>/', views.pnprlps_mapping, name='pnprlps_mapping'),
  path('data-panel/tps_mapping/<int:current_product_category_id>/', views.tps_mapping, name='tps_mapping'),
  path('data-panel/pyps_mapping/<int:current_product_category_id>/', views.pyps_mapping, name='pyps_mapping'),
  path('data-panel/oed_mapping/<int:user_dept_id>/', views.oed_mapping, name='oed_mapping'),

  path('data-panel/vdm/tech_data/<int:technology_id>/', views.tech_data, name='tech_data'),
  path('data-panel/vdm/view_pns_of_ps/<int:production_station_id>/', views.view_pns_of_ps, name='view_pns_of_ps'),
  path('data-panel/vdm/view_tools_of_ps/<int:production_station_id>/', views.view_tools_of_ps, name='view_tools_of_ps'),
  path('data-panel/vdm/view_pys_of_ps/<int:production_station_id>/', views.view_pys_of_ps, name='view_pys_of_ps'),
  path('data-panel/vdm/view_pns_of_model/<int:model_id>/', views.view_pns_of_model, name='view_pns_of_model'),
  path('data-panel/vdm/view_pls_of_pn/<int:part_number_id>/', views.view_pls_of_pn, name='view_pls_of_pn'),
  path('data-panel/vdm/tool_data/<int:tool_id>/', views.tool_data, name='tool_data'),
  path('data-panel/vdm/poka_yoke_data/<int:poka_yoke_id>/', views.poka_yoke_data, name='poka_yoke_data'),
  path('data-panel/vdm/py_data/delete_pyps_map/<int:pyps_map_id>/', views.delete_pyps_map, name='delete_pyps_map'),
  path('data-panel/vdm/tps_data/<int:tps_map_id>/tps_life_param_edit/', views.tps_life_param_edit, name='tps_life_param_edit'),
  path('data-panel/vdm/tps_data/<int:tps_map_id>/tp_map/<int:edit_type>/', views.tps_part_numbers_map_edit, name='tps_part_numbers_map_edit'),
  path('data-panel/vdm/tps_data/<int:tps_map_id>/tps_image_edit/', views.tps_image_edit, name='tps_image_edit'),
  path('data-panel/vdm/oee_events/<int:current_dept_id>/', views.dp_oee_event, name='dp_oee_event'),

  path('ajax_load_all_users/', views.ajax_load_all_users, name='ajax_load_all_users'),
  path('ajax_load_operators/', views.ajax_load_operators, name='ajax_load_operators'),
  path('ajax_load_empty_option/', views.ajax_load_empty_option, name='ajax_load_empty_option'),
  path('ajax_load_product_technologies/', views.ajax_load_product_technologies, name='ajax_load_product_technologies'),
  path('ajax_load_product_models/', views.ajax_load_product_models, name='ajax_load_product_models'),
  path('ajax_load_product_models_of_pl/', views.ajax_load_product_models_of_pl, name='ajax_load_product_models_of_pl'),
  path('ajax_load_product_models_of_ps/', views.ajax_load_product_models_of_ps, name='ajax_load_product_models_of_ps'),
  path('ajax_load_product_models_of_pls/', views.ajax_load_product_models_of_pls, name='ajax_load_product_models_of_pls'),
  path('ajax_load_product_models_of_pl_qa_pcs/', views.ajax_load_product_models_of_pl_qa_pcs, name='ajax_load_product_models_of_pl_qa_pcs'),
  path('ajax_load_production_lines/', views.ajax_load_production_lines, name='ajax_load_production_lines'),
  path('ajax_load_production_lines_of_qa_pcss/', views.ajax_load_production_lines_of_qa_pcss, name='ajax_load_production_lines_of_qa_pcss'),
  path('ajax_load_department_of_wfs/', views.ajax_load_department_of_wfs, name='ajax_load_department_of_wfs'),
  path('ajax_load_dept_users_of_wfs/', views.ajax_load_dept_users_of_wfs, name='ajax_load_dept_users_of_wfs'),
  path('ajax_load_production_lines_of_tools/', views.ajax_load_production_lines_of_tools, name='ajax_load_production_lines_of_tools'),
  path('ajax_load_production_lines_of_pn/', views.ajax_load_production_lines_of_pn, name='ajax_load_production_lines_of_pn'),
  path('ajax_load_production_stations/', views.ajax_load_production_stations, name='ajax_load_production_stations'),
  path('ajax_load_production_stations_of_pl_tools/', views.ajax_load_production_stations_of_pl_tools, name='ajax_load_production_stations_of_pl_tools'),
  path('ajax_load_part_numbers/', views.ajax_load_part_numbers, name='ajax_load_part_numbers'),
  path('ajax_load_part_numbers_of_ps/', views.ajax_load_part_numbers_of_ps, name='ajax_load_part_numbers_of_ps'),
  path('ajax_load_part_number_map_data/', views.ajax_load_part_number_map_data, name='ajax_load_part_number_map_data'),
  path('ajax_load_part_numbers_of_ps/', views.ajax_load_part_numbers_of_ps, name='ajax_load_part_numbers_of_ps'),
  path('ajax_load_part_numbers_of_pl_m/', views.ajax_load_part_numbers_of_pl_m, name='ajax_load_part_numbers_of_pl_m'),
  path('ajax_load_part_numbers_of_ps_m/', views.ajax_load_part_numbers_of_ps_m, name='ajax_load_part_numbers_of_ps_m'),
  path('ajax_load_part_numbers_of_pls_ms/', views.ajax_load_part_numbers_of_pls_ms, name='ajax_load_part_numbers_of_pls_ms'),
  path('ajax_load_part_numbers_of_pl_m_qa_pcs/', views.ajax_load_part_numbers_of_pl_m_qa_pcs, name='ajax_load_part_numbers_of_pl_m_qa_pcs'),
  path('ajax_load_part_numbers_of_tps/', views.ajax_load_part_numbers_of_tps, name='ajax_load_part_numbers_of_tps'),
  path('ajax_load_child_part_numbers/', views.ajax_load_child_part_numbers, name='ajax_load_child_part_numbers'),
  path('ajax_load_child_part_numbers_of_pn/', views.ajax_load_child_part_numbers_of_pn, name='ajax_load_child_part_numbers_of_pn'),
  path('ajax_load_child_part_numbers_of_pns/', views.ajax_load_child_part_numbers_of_pns, name='ajax_load_child_part_numbers_of_pns'),
  path('ajax_load_qa_pcss_of_production_line/', views.ajax_load_qa_pcss_of_production_line, name='ajax_load_qa_pcss_of_production_line'),
  path('ajax_load_product_rejection_reasons/', views.ajax_load_product_rejection_reasons, name='ajax_load_product_rejection_reasons'),
  path('ajax_load_tools/', views.ajax_load_tools, name='ajax_load_tools'),
  path('ajax_load_tools_of_ps/', views.ajax_load_tools_of_ps, name='ajax_load_tools_of_ps'),
  path('ajax_load_poka_yokes/', views.ajax_load_poka_yokes, name='ajax_load_poka_yokes'),
  
  path('accounts/user-registration-done/', views.UserRegistrationDoneView.as_view(), name='user_registration_done'),
  path('accounts/login-user-approval-await/', views.UserApprovalAwaitView.as_view(), name='user_approval_await'),
  path('accounts/autn-user-access-denied/', views.UserAccessDeniedView.as_view(), name='user_access_denied'),

  path('under-development/', views.UnderDevelopmentView.as_view(), name='under_development'),

]
