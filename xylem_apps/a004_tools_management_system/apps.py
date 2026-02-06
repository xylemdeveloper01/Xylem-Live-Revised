from django.apps import AppConfig


class A004ToolsManagementSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xylem_apps.a004_tools_management_system'

    def ready(self):
        import xylem_apps.a004_tools_management_system.signals
