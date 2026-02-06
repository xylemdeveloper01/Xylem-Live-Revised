import math, time, datetime, logging
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q, Sum, Max
from django.db.models.functions import Coalesce
from django.core.cache import caches

from xylem.settings import EMAIL_HOST_USER, XYLEM_MODE, XYLEM_MODE_DIC
from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import TPsMapping
from xylem_apps.a007_oee_monitoring.models import ProductionChangeOvers

from .models import ToolHistoryLog, ToolAlert


a004_logger = logging.getLogger(serve.an_tools_management_system)
a004_production_interruption_dict = {}
current_send_alert_th = None

a007_cache = caches[serve.an_oee_monitoring]


def get_tool_consumption_data_dict(tps_map = None, tps_map_id= None): # get tool life count
    oee_dict = a007_cache.get(serve.Apps.A007OEEMonitoring.cache_key_of_oee_dict)
    if tps_map_id:
        tps_map = TPsMapping.objects.get(tps_map_id)
    thl = ToolHistoryLog.objects.filter(tps_map=tps_map)
    pl = serve.get_production_line_of_ps(production_station = tps_map.production_station_i)
    pns_of_tps = serve.get_part_numbers_of_tps(tps_map=tps_map)
    if thl.exists():
        thl_latest = thl.latest("boosted_time")
        thl_last_cho = thl.latest("boosted_time").boosted_change_over
        thl_last_pq_offset = thl_latest.pq_offset
        if thl_last_cho:
            temp_change_overs = ProductionChangeOvers.objects.filter(
                Q(part_number_i__in=list(pns_of_tps)) | Q(part_number_i=None), 
                Q(production_line_i=pl),
                ~Q(end_time=None),
                Q(start_time__gt=thl_last_cho.start_time),
                ~Q(id=thl_last_cho.id),
            )
            total_pq = temp_change_overs.aggregate(total_pq = Coalesce(Sum("pq"), 0))["total_pq"] - thl_last_pq_offset
        else:
            temp_change_overs = ProductionChangeOvers.objects.filter(
                Q(part_number_i__in=list(pns_of_tps)) | Q(part_number_i=None), 
                Q(production_line_i=pl),
                Q(start_time__gt=tps_map.datetime_mapped),
                ~Q(end_time=None),
            )
            total_pq = temp_change_overs.aggregate(total_pq = Coalesce(Sum("pq"), 0))["total_pq"] - thl_last_pq_offset
    else:
        temp_change_overs = ProductionChangeOvers.objects.filter(
            Q(part_number_i__in=list(pns_of_tps)) | Q(part_number_i=None), 
            Q(production_line_i=pl),
            Q(start_time__gt=tps_map.datetime_mapped),
            ~Q(end_time=None),
        )
        total_pq = temp_change_overs.aggregate(total_pq = Coalesce(Sum("pq"), 0))["total_pq"]
    if temp_change_overs.exists():
        latest_cho = temp_change_overs.latest('start_time')
    else:
        latest_cho = None
    ongoing_consumption = 0
    if pl.icode in oee_dict:
        if not oee_dict[pl.icode]["rpn_i"]:
            ongoing_consumption = oee_dict[pl.icode]["spq"] - oee_dict[pl.icode]["spq_upto_lcho"]
        elif oee_dict[pl.icode]["rpn_i"] in pns_of_tps:
            ongoing_consumption = oee_dict[pl.icode]["spq"] - oee_dict[pl.icode]["spq_upto_lcho"]
    return {
        "consumed_life" : math.ceil((total_pq + ongoing_consumption)/tps_map.parts_freq) if tps_map.parts_freq else total_pq + ongoing_consumption,
        "ongoing_consumption" : math.ceil(ongoing_consumption/tps_map.parts_freq) if tps_map.parts_freq else ongoing_consumption,
        "latest_cho" : latest_cho,
    }


def get_tps_map_with_param(tps_map = None, tps_map_id = None):
    if tps_map_id:
        tps_map = TPsMapping.objects.get(id = int(tps_map_id))
    consumption_data_dict = get_tool_consumption_data_dict(tps_map)
    avl_tool_life = tps_map.full_life-consumption_data_dict["consumed_life"]
    avl_life_percent = serve.convert_float_with_int_possibility(int((avl_tool_life/tps_map.full_life)*100*10)/10, 1)
    return {
        "tps_map":tps_map, "ongoing_consumption": consumption_data_dict["ongoing_consumption"],
        "latest_cho": consumption_data_dict["latest_cho"], "avl_tool_life": avl_tool_life,
        "avl_life_percent": avl_life_percent, "in_low_life": avl_tool_life<=tps_map.low_life_consideration
    }


def get_tps_maps_with_low_life_by_pc(product_category = None, product_category_id = None, tool_type = None, tool_type_id = None):
    tps_maps = TPsMapping.objects.filter(tool_i__in=serve.get_tools(product_category=product_category, product_category_id=product_category_id, tool_type=tool_type, tool_type_id = tool_type_id)).order_by("tool_i_id")
    tps_map_list = []
    for tps_map in tps_maps:
        tps_map_with_param = get_tps_map_with_param(tps_map)
        if tps_map_with_param["in_low_life"]:
            tps_map_list.append(tps_map_with_param)
    return tps_map_list


def get_tps_map_list_with_param_by_pl_or_tool(pl_or_tool = None, pl_or_tool_id = None, tool_type = None, tool_type_id = None):
    if pl_or_tool:
        pl_or_tool_id = pl_or_tool.icode
    pl_or_tool_id = int(pl_or_tool_id)
    temp_remainder = (pl_or_tool_id-serve.IcodeSplitup.product_category["from"])%serve.IcodeSplitup.product_category["period"]
    if serve.IcodeSplitup.production_lines["from_in_category"]<= temp_remainder < serve.IcodeSplitup.production_lines["to_in_category"]:
        if tool_type:
            tool_type_id = tool_type.icode
        tool_type_id = int(tool_type_id)
        product_category_id = serve.get_product_category_by_item(item_id=pl_or_tool_id).icode
        if tool_type_id == serve.Others.tool_tools.icode:
            tps_maps = TPsMapping.objects.filter(
                production_station_i__in = serve.get_production_stations(production_line_id=pl_or_tool_id),
                tool_i_id__gte=product_category_id+serve.IcodeSplitup.tool_tools["from_in_category"],
                tool_i_id__lte=product_category_id+serve.IcodeSplitup.tool_tools["to_in_category"]
            ).order_by('production_station_i')
        else:
            tps_maps = TPsMapping.objects.filter(
                production_station_i__in = serve.get_production_stations(production_line_id=pl_or_tool_id),
                tool_i_id__gte=product_category_id+serve.IcodeSplitup.tool_fixtures["from_in_category"],
                tool_i_id__lte=product_category_id+serve.IcodeSplitup.tool_fixtures["to_in_category"]
            ).order_by('production_station_i')
    else:
        tps_maps = TPsMapping.objects.filter(tool_i_id = pl_or_tool_id).order_by('tool_i')
    tps_map_list = []
    for tps_map in tps_maps:
        tps_map_list.append(get_tps_map_with_param(tps_map))
    return tps_map_list
