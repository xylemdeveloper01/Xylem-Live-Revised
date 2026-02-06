from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from . import serve 

from .models import UserProfile, UserExtraFields, TPsMapping, TPsmapPnExMapping, DataPanelActivity
from .utils import get_current_user 

previous_instance_data_dic = {}

@receiver(post_save, sender=UserProfile)
def create_user_approval(sender, instance, created, **kwargs):
    if created:
        UserExtraFields.objects.create(user=instance)


@receiver(pre_save, sender=TPsMapping)
def store_previous_instance(sender, instance, **kwargs):
    if instance.pk:  # Check if the instance already exists (it's an update, not a create)
        previous_instance = sender.objects.get(pk=instance.pk)
        # Store the previous state in a global variable
        previous_instance_data_dic[sender.__name__ + str(instance.pk)] = previous_instance


@receiver(post_save, sender=TPsMapping)
def signal_of_tps_map_update(sender, instance, created, **kwargs):
    if not created:
        previous_instance = previous_instance_data_dic[sender.__name__ + str(instance.pk)]
        param_change_action_list = []
        if previous_instance.full_life != instance.full_life:
            param_change_action_list.append(f"Tool's full life change from {previous_instance.full_life} to {instance.full_life}")
        if previous_instance.low_life_consideration != instance.low_life_consideration:
            param_change_action_list.append(f" Tool's low life consideration life changed from {previous_instance.low_life_consideration} to {instance.low_life_consideration}")
        if previous_instance.parts_freq != instance.parts_freq:
            param_change_action_list.append(f" Parts frequency changed from {previous_instance.parts_freq} to {instance.parts_freq}")
        if previous_instance.tool_image.url != instance.tool_image.url:
            param_change_action_list.append(f" Image changed from {previous_instance.tool_image.url} to {instance.tool_image.url}")
        param_change_action_list.append(instance.tool_i.name + " at " + serve.get_pl_ps_display_format(production_station=instance.production_station_i))
        user = get_current_user()
        DataPanelActivity.objects.create(
            relevant_user=user,
            model_name=sender.__name__,  
            model_object_id=instance.id,  
            action=" ".join(param_change_action_list),
        )
        del previous_instance


@receiver(post_save, sender=TPsmapPnExMapping)
def signal_of_tps_pn_ex_map_create(sender, instance, created, **kwargs):
    if created:
        temp_action_str = "Part number "+ instance.part_number_i.name + " excluded for "+\
            instance.tps_map.tool_i.name + " at "  +\
            serve.get_production_line_of_ps(instance.tps_map.production_station_i).name + ": " +\
            instance.tps_map.production_station_i.name
        user = get_current_user()
        DataPanelActivity.objects.create(
            relevant_user=user,
            model_name=sender.__name__,  
            model_object_id=instance.id,  
            action=temp_action_str,
        )


@receiver(post_delete, sender=TPsmapPnExMapping)
def signal_of_tps_pn_ex_map_delete(sender, instance, **kwargs):
    temp_action_str = "Part number "+ instance.part_number_i.name + " included for "+\
        instance.tps_map.tool_i.name + " at "  +\
        serve.get_production_line_of_ps(instance.tps_map.production_station_i).name + ": " +\
        instance.tps_map.production_station_i.name
    user = get_current_user()
    DataPanelActivity.objects.create(
        relevant_user=user,
        model_name=sender.__name__,  
        model_object_id=instance.id,  
        action=temp_action_str,
    )


from django.db.models.signals import pre_delete
from django.dispatch import receiver

from xylem_apps.a000_xylem_master.models import PyPsMapping

from xylem_apps.a010_poka_yoke_monitoring.models import PokaYokeInspections


@receiver(pre_delete, sender=PyPsMapping)
def delete_related_inspections(sender, instance, **kwargs):
    a = PokaYokeInspections.objects.using('a010_poka_yoke_monitoring').filter(pyps_map=instance)
    print(a.count())
    # a.delete()