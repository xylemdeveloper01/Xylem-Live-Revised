from django.apps import AppConfig


class A000XylemMasterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xylem_apps.a000_xylem_master'

    def ready(self):
        import xylem_apps.a000_xylem_master.signals


