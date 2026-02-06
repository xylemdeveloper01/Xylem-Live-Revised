from django.apps import AppConfig


class A010PokaYokeMonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xylem_apps.a010_poka_yoke_monitoring'

    # def ready(self):
    #     import xylem_apps.a010_poka_yoke_monitoring.signals
