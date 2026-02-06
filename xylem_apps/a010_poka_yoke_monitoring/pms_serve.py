import time, datetime, logging
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q, F, Sum, Max
from django.db.models.functions import Cast, Coalesce, TruncDate

from xylem_apps.a000_xylem_master import serve
from xylem_apps.a000_xylem_master.models import PyPsMapping

from .models import PokaYokeInspections

a010_logger = logging.getLogger(serve.an_poka_yoke_monitoring)

          
def get_pyps_maps_of_awaiting_inspections(product_category = None, product_category_id = None):
    pyps_maps_pc = PyPsMapping.objects.filter(poka_yoke_i__in = list(serve.get_poka_yokes(product_category=product_category, product_category_id=product_category_id)))
    today_date = datetime.datetime.now().date()
    pyps_inspections_await = pyps_maps_pc.exclude(
        id__in = list(
            PokaYokeInspections.objects.filter(
                pyps_map__in = list(pyps_maps_pc),
                inspection_due_date__gte = today_date,
            ).values_list('pyps_map', flat=True)
        )
    )
    return pyps_inspections_await


def get_poka_yoke_tree_dict_of_pc(product_category = None, product_category_id = None):
    if product_category:
        product_category_id = product_category.icode
    return serve.get_from_background_worker_api(serve.a010_get_poka_yoke_tree_dict_of_pc_url+str(product_category_id)).json()


def get_poka_yoke_fruit_clusters_dict(production_line_id):
	return serve.get_from_background_worker_api(serve.a010_get_poka_yoke_fruit_clusters_dict_url+str(production_line_id)).json()


def get_poka_yoke_fruits_dict(production_station_id):
    return serve.get_from_background_worker_api(serve.a010_get_poka_yoke_fruits_dict_url+str(production_station_id)).json()
