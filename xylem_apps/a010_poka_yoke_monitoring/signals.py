# from django.db.models.signals import pre_delete
# from django.dispatch import receiver

# from xylem_apps.a000_xylem_master.models import PyPsMapping

# from .models import PokaYokeInspections


# @receiver(pre_delete, sender=PyPsMapping)
# def delete_related_inspections(sender, instance, **kwargs):
#     a = PokaYokeInspections.objects.using('a010_poka_yoke_monitoring').filter(pyps_map=instance)
#     print(a.count)
#     # a.delete()