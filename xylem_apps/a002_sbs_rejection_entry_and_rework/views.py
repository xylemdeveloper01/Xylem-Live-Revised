import datetime, json
from collections import defaultdict, Counter
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils.timezone import make_aware
from django.db.models import Q,F,Count

import xylem.custom_messages.constants as custom_messages
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom, view_eligibity_test
from xylem_apps.a000_xylem_master import serve 

from xylem_apps.a000_xylem_master.models import Icodes, PnMTMapping

from .forms import RejectionReworkEntryForm
from .models import RejectionReworkEntryData, PackingInterlockData

# Create your views here.
@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.Inprocess_QA, serve.Designations.All_designations],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def qa_rejection_rework_form(request):
	form=RejectionReworkEntryForm(request.POST or None)
	if request.method == "POST":
		if form.is_valid():
			part_number = form.cleaned_data["part_number"]
			production_line = form.cleaned_data["production_line"]
			production_station = form.cleaned_data["production_station"]
			rejection_reason = form.cleaned_data["rejection_reason"]
			part_status = form.cleaned_data["part_status"]
			for barcode in request.POST.get("added_barcodes").split("\n"):
				rre_obj=RejectionReworkEntryData.objects.create(
					part_number_i=part_number,
					production_line_i=production_line,
					production_station_i=production_station,
					rejection_reason_i=rejection_reason,
					part_status_i=part_status,
					barcode_data=barcode.strip(),
					booked_user=request.user,
				)
				PackingInterlockData.objects.create(
					entry_ref=rre_obj,
					barcode_data=rre_obj.barcode_data,
					part_status_i=rre_obj.part_status_i,  
					datetime=rre_obj.booked_datetime,  
				)
			messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, f"{rre_obj.part_status_i.name} data added successfully")
			return redirect("a002:qa_rejection_rework_form")
		else:
			error_msg=""
			for field, errors in form.errors.as_data().items():
				error_msg= error_msg+";".join(errors[0].messages)
			messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, error_msg)
			return redirect("a002:qa_rejection_rework_form")
	context = {
		"parent" : "Entry Forms",
		"segment" : "QA Rejection and Rework Entry Form",
		"form" : form
	}
	return render(request,"a002/qa_rejection_rework_form.html", context)


@login_required(login_url="/accounts/login/")
def rre_validate_barcode(request):
	if 'bc' in request.GET:
		barcode = request.GET.get('bc')
		barcode_exists = PackingInterlockData.objects.filter(barcode_data=barcode).exists()
		part_number = Icodes.objects.get(icode=int(request.GET.get('pn_id')))
		check = None
		if serve.remove_space(part_number.name) in serve.remove_space(barcode):
			check = True
		check = True # Bypass for part number match check
		return JsonResponse({'barcode_pn_check':check ,'barcode_exists': barcode_exists})
	

@login_required(login_url="login")
def qa_rejection_rework_report(request, current_product_category_id):
    product_categories = serve.get_product_categories()
    current_product_category = product_categories.get(icode = current_product_category_id)
    context = {
		"parent": "reports",
		"segment" : "QA Rejection and Rework Report",	  
		"production_lines": serve.get_production_lines(product_category_id = current_product_category_id),       
        "shifts" : serve.get_shifts(),
		"part_status" : serve.get_part_status_rejection_and_rework(),
        "current_product_category" : current_product_category,
        "product_categories": product_categories       
	}    
    return render(request, 'a002/qa_rejection_rework_report.html', context)


@login_required(login_url="login")
def qa_rejection_rework_graphical_report(request, current_product_category_id):
    product_categories = serve.get_product_categories()
    current_product_category = product_categories.get(icode = current_product_category_id)
    entry_data_objects = RejectionReworkEntryData.objects.filter(production_line_i__in=list(serve.get_production_lines(product_category_id=current_product_category_id)))
    pnmt_objects = PnMTMapping.objects.filter(technology_i__in=list(serve.get_product_technologies(product_category_id=current_product_category_id)))
    get_shift_data = serve.get_shifts()
    booked_times = [time.booked_datetime for time in entry_data_objects]
    print(booked_times)
    time_range = [
     	(serve.Shifts.ShiftA.start_time, serve.Shifts.ShiftA.ns_start_time),
     	(serve.Shifts.ShiftB.start_time, serve.Shifts.ShiftB.ns_start_time),
     	(serve.Shifts.ShiftC.start_time, serve.Shifts.ShiftC.ns_start_time),
    ]
    shift_data = []
    shift_name_counts = defaultdict(int)

    for booked_time in booked_times:
        shift_counts = defaultdict(int)              
        for start_time, end_time in time_range:
            if start_time <= end_time:
                if start_time <= booked_time.time() <= end_time:
                    shift_id = get_shift_data[time_range.index((start_time, end_time))].icode
                    shift_name = get_shift_data[time_range.index((start_time, end_time))].name
                    shift_counts[(shift_id, shift_name)] += 1
            else:
                if start_time <= booked_time.time() <= end_time or \
                   booked_time.time() >= start_time or \
                   booked_time.time() <= end_time:
                    shift_id = get_shift_data[time_range.index((start_time, end_time))].icode
                    shift_name = get_shift_data[time_range.index((start_time, end_time))].name
                    shift_counts[(shift_id, shift_name)] += 1

        for (id, name), count in shift_counts.items():
            shift_name_counts[(id, name)] += count

    for (id, name), count in shift_name_counts.items():
        shift_data.append({"shift": id, "name": name, "count": count})

    date_field = []
    month_field = []
    date_obj = entry_data_objects.values_list("booked_datetime").all() 
    date_list = [date[0] for date in date_obj]
    for i in date_list:
        if i.time() < shift_start_time :
            adjusted_date = i.date() - datetime.timedelta(days=1)  
            date_field.append(adjusted_date)
            month_field.append(adjusted_date)

        else:
            date_field.append(i.date())
            month_field.append(i.date())

    date_counts = Counter(date_field)
    formatted_date_counts = [{"truncated_date": date, "count": count} for date, count in date_counts.items()]

    month_counts = Counter(month_field)
    month_counts = [{"truncated_month": month, "count": count} for month, count in month_counts.items()]
    
    summed_counts = defaultdict(int)

    for entry in month_counts:
        truncated_month = entry['truncated_month'].replace(day=1) 
        summed_counts[truncated_month] += entry['count']

    summed_month_counts = [{'truncated_month': month, 'count': count} for month, count in summed_counts.items()]

    part_numbers = list(entry_data_objects.values_list("part_number_i_id", flat=True))

    technology_count_dict = defaultdict(int)

    for part_number in part_numbers:
        technology = (
            pnmt_objects.filter(part_number_i_id=part_number)
            .values("technology_i_id")
            .annotate(count=Count("technology_i_id"))
            .order_by()
        )
        for tech in technology:
            technology_count_dict[tech['technology_i_id']] += tech['count']

    technology_count = [
        {"technology_i_id": tech_id, "count": count}
        for tech_id, count in technology_count_dict.items()
    ]
    line_counts = entry_data_objects.values("production_line_i_id").annotate(
        count=Count("production_line_i_id")
    )
    reason_counts = entry_data_objects.values("rejection_reason_i_id").annotate(
        count=Count("rejection_reason_i_id")
    )
    status_counts = entry_data_objects.values("part_status_i_id").annotate(
        count=Count("part_status_i_id")
    )
    date_list = [
        {"date": item["truncated_date"].strftime("%Y-%m-%d"), "count": item["count"]}
        for item in formatted_date_counts
    ]
    month_list = [
        {"month": item["truncated_month"].strftime("%Y-%m"), "count": item["count"]}
        for item in summed_month_counts
    ]
    technology_list = [
        {"technology_i_id": item["technology_i_id"], "count": item["count"]}
        for item in technology_count
    ]
    line_list = [
        {"production_line_i_id": item["production_line_i_id"], "count": item["count"]}
        for item in line_counts
    ]
    reason_list = [
        {"rejection_reason_i_id": item["rejection_reason_i_id"], "count": item["count"]}
        for item in reason_counts
    ]

    status_list = [
        {"part_status_i_id": item["part_status_i_id"], "count": item["count"]}
        for item in status_counts
    ]
    
    technology_codes = [item["technology_i_id"] for item in technology_list]
    technology_names = Icodes.objects.filter(Q(icode__in=technology_codes)).values(
        "icode", "name"
    )
    technology_mapping = {item["icode"]: item["name"] for item in technology_names}

    line_codes = [item["production_line_i_id"] for item in line_list]
    line_names = Icodes.objects.filter(Q(icode__in=line_codes)).values("icode", "name")
    line_mapping = {item["icode"]: item["name"] for item in line_names}

    reason_codes = [item["rejection_reason_i_id"] for item in reason_list]
    reason_names = Icodes.objects.filter(Q(icode__in=reason_codes)).values(
        "icode", "name"
    )
    reason_mapping = {item["icode"]: item["name"] for item in reason_names}

    status_codes = [item["part_status_i_id"] for item in status_list]
    status_names = Icodes.objects.filter(Q(icode__in=status_codes)).values(
        "icode", "name"
    )
    status_mapping = {item["icode"]: item["name"] for item in status_names}

    technology_with_names = sorted(
        [
            {
                "technology_i_id": item["technology_i_id"],
                "name": technology_mapping.get(
                    item["technology_i_id"], item["technology_i_id"]
                ),
                "count": item["count"],
            }
            for item in technology_list
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    line_with_names = sorted(
        [
            {
                "production_line_i_id": item["production_line_i_id"],
                "name": line_mapping.get(
                    item["production_line_i_id"], item["production_line_i_id"]
                ),
                "count": item["count"],
            }
            for item in line_list
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    reason_with_names = sorted(
        [
            {
                "rejection_reason_i_id": item["rejection_reason_i_id"],
                "name": reason_mapping.get(
                    item["rejection_reason_i_id"], item["rejection_reason_i_id"]
                ),
                "count": item["count"],
            }
            for item in reason_list
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    status_with_names = sorted(
        [
            {
                "part_status_i_id": item["part_status_i_id"],
                "name": status_mapping.get(
                    item["part_status_i_id"], item["part_status_i_id"]
                ),
                "count": item["count"],
            }
            for item in status_list
        ],
        key=lambda x: x["count"],
        reverse=True,
    )
    # print(technology_with_names)
    # print(line_with_names)
    day_counts_json = json.dumps(date_list)
    month_counts_json = json.dumps(month_list)
    technology_counts_json = json.dumps(technology_with_names)
    line_counts_json = json.dumps(line_with_names)
    reason_counts_json = json.dumps(reason_with_names)
    status_counts_json = json.dumps(status_with_names)
    shift_data_json = json.dumps(shift_data)
    context = {
		"segment": "QA Rejection and Rework Graphical Report",
		"current_product_category":current_product_category,
        "product_categories":product_categories,
        "day_counts": day_counts_json,
        "month_counts": month_counts_json,
        "technology_counts": technology_counts_json,
        "technology_names": technology_with_names,
        "line_counts": line_counts_json,
        "line_names": line_with_names,
        "reason_counts": reason_counts_json,
        "reason_names": reason_with_names,
        "status_counts": status_counts_json,
        "status_names": status_with_names,
        "shift_counts": shift_data_json,
        "shift_names": shift_data,
    }
    return render(request, "a002/qa_rejection_rework_graphical_report.html", context)

	
@login_required(login_url="login")
def ajax_load_report_table(request, current_product_category_id):
    production_line_id = request.GET.get('production_line_id')
    start_date = request.GET.get('from_date')
    end_date = request.GET.get('to_date')
    shift_id = request.GET.get('shift_id')
    part_status_id = request.GET.get('part_status_id')

    # Convert dates from string
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

    filtered_data = RejectionReworkEntryData.objects.filter(
        booked_datetime__gte = serve.Shifts.ShiftA.start_date_time(start_date),
        booked_datetime__lt = serve.Shifts.ShiftC.ns_start_date_time(end_date),
    )

    if production_line_id:
        production_lines = [serve.get_icode_object(production_line_id)]
        filtered_data = filtered_data.filter(production_line_i__in = production_lines)
    else:
        production_lines = serve.get_production_lines(product_category_id = current_product_category_id)

    if part_status_id:
        part_statuses = [serve.get_icode_object(part_status_id)]
        filtered_data = filtered_data.filter(part_status_i__in = part_statuses)
    else:
        part_statuses = serve.get_part_status_rejection_and_rework()
        

    if shift_id:
        shift = serve.get_icode_object(shift_id)
        if shift.icode == serve.IcodeSplitup.icode_shiftC:
            shift = serve.Shifts.ShiftC
            filtered_data = filtered_data.filter(Q(booked_datetime__time__gte = shift.start_time) | Q(booked_datetime__time__lt = shift.ns_start_time))
        else:
            shift = serve.Shifts.ShiftA if shift.icode == serve.IcodeSplitup.icode_shiftA else serve.Shifts.ShiftB
            filtered_data = filtered_data.filter(booked_datetime__time__gte = shift.start_time, booked_datetime__time__lt = shift.ns_start_time)
        shifts = [shift]
    else:
        shifts = serve.get_shifts()
        filtered_data = filtered_data

    # Handle no data found scenario
    if not filtered_data.exists():
        messages.add_message(request, custom_messages.INFO_DISMISSABLE, mark_safe(f"No Rejection & Rework Entry available for the selected period and filters"))
        return render(request, 'msg_templates/messages.html')

    # Render the context with filtered data
    context = {
        "production_lines": production_lines,
        "shifts": shifts,
        "part_statuses": part_statuses,
        "period": f"{serve.get_standard_str_format_of_dt_or_d(d=start_date)} - {serve.get_standard_str_format_of_dt_or_d(d=end_date)}",
        "filtered_data": filtered_data,
    }
    return render(request, 'a002/ajax_report_table.html', context)


@login_required(login_url="login")
def ajax_load_graph_data(request):
    from_date = request.GET.get("from_date", None)
    to_date = request.GET.get("to_date", None)
    selected_technology = request.GET.get("technology", None)
    selected_line = request.GET.get("line", None)
    selected_reason = request.GET.get("reason", None)
    selected_shift = request.GET.get("shift", None)
    selected_status = request.GET.get("status", None)

    shift_data = []
    sel_shift_data = []
    rerw_forms=[]

    # Initialize filters
    filters = {}
    if selected_line:
        filters["production_line_i_id"] = selected_line
    if selected_reason:
        filters["rejection_reason_i_id"] = selected_reason
    if selected_status:
        filters["part_status_i_id"] = selected_status
    if from_date and to_date:
        filters["booked_datetime__range"] = [make_aware(datetime.datetime.fromisoformat(from_date)), make_aware(datetime.datetime.fromisoformat(to_date))]

    # Apply filters to the base queryset
    base_queryset = RejectionReworkEntryData.objects.filter(**filters)
    print(base_queryset)

    if selected_technology:
        mapping_objects = list(PnMTMapping.objects.filter(technology_i_id=selected_technology).values_list("part_number_i_id", flat=True))
        base_queryset = base_queryset.filter(part_number_i_id__in=mapping_objects)

    shift_name_counts = defaultdict(int)
    shift_id_mapping = defaultdict(set)

   
    # Get shift data
    get_shift_data = serve.get_shifts()
    time_ranges = {
        'ShiftA': (serve.Shifts.ShiftA.start_time, serve.Shifts.ShiftB.start_time),
        'ShiftB': (serve.Shifts.ShiftB.start_time, serve.Shifts.ShiftC.start_time),
        'ShiftC': (serve.Shifts.ShiftC.start_time, serve.Shifts.ShiftA.start_time)
    }

    # Create a dictionary for easy lookup of shift names and ids
    shift_lookup = {range_: (shift.icode, shift.name) for shift, range_ in zip(get_shift_data, time_ranges.values())}

    # Process booked times and shifts
    booked_times = list(base_queryset.values_list('booked_datetime', flat=True))
    time_to_id_map = {obj.booked_datetime.time(): obj.id for obj in base_queryset}

        
    for booked_time in booked_times:
        booked_id = time_to_id_map.get(booked_time.time())
        if booked_id:
            for shift_name, (start_time, end_time) in time_ranges.items():
                if start_time <= end_time:  # Normal shift range
                    if start_time <= booked_time.time() <= end_time:
                        shift_id, shift_name = shift_lookup[(start_time, end_time)]
                        shift_id_mapping[(shift_id, shift_name)].add(booked_id)
                        shift_name_counts[(shift_id, shift_name)] += 1
                else:  # Shift range spans midnight
                    if booked_time.time() >= start_time or booked_time.time() <= end_time:
                        shift_id, shift_name = shift_lookup[(start_time, end_time)]
                        shift_id_mapping[(shift_id, shift_name)].add(booked_id)
                        shift_name_counts[(shift_id, shift_name)] += 1
    # Generate shift data
    shift_data = [
        {"shift": shift_id, "name": shift_name, "entry_ids": list(entry_ids), "count": shift_name_counts[(shift_id, shift_name)]}
        for (shift_id, shift_name), entry_ids in shift_id_mapping.items()
    ]
    if selected_shift:
        # Filter RejectionReworkEntryData objects based on the selected shift
        shift_id = int(selected_shift)
        entry_ids_to_query = []
        for shift_item in shift_data:
            if shift_item['shift'] == shift_id:
                entry_ids_to_query = shift_item['entry_ids']
                shift_name = shift_item['name']
                break

        if entry_ids_to_query:
            rerw_forms = RejectionReworkEntryData.objects.filter(id__in=entry_ids_to_query)
            sel_shift_data = [
                {"shift": shift_id, "name": shift_name, "count": shift_name_counts[(shift_id, shift_name)]}
            ]
    else:
        rerw_forms = base_queryset
        sel_shift_data = [
            {"shift": shift_id, "name": shift_name, "entry_ids": list(entry_ids), "count": shift_name_counts[(shift_id, shift_name)]}
            for (shift_id, shift_name), entry_ids in shift_id_mapping.items()
        ]

    #  Ensure `filtered_data` is a queryset before calling `values_list()`
    if isinstance(rerw_forms, list):
        # If it's a list, convert it to a queryset
        filtered_data = RejectionReworkEntryData.objects.filter(id__in=[obj.id for obj in rerw_forms])
    else:
        filtered_data = rerw_forms

    date_field = []
    month_field = []
    date_obj = filtered_data.values_list("booked_datetime").all() 
    date_list = [date[0] for date in date_obj]
    for i in date_list:
        if i.time() < serve.Shifts.ShiftA.start_time:
            adjusted_date = i.date() - datetime.timedelta(days=1)
            date_field.append(adjusted_date)
            month_field.append(adjusted_date)
        else:
            date_field.append(i.date())
            month_field.append(i.date())

    date_counts = Counter(date_field)
    formatted_date_counts = [{"truncated_date": date, "count": count} for date, count in date_counts.items()]

    month_counts = Counter(month_field)
    month_counts = [{"truncated_month": month, "count": count} for month, count in month_counts.items()]
    
    summed_counts = defaultdict(int)
    for entry in month_counts:
        truncated_month = entry['truncated_month'].replace(day=1) 
        summed_counts[truncated_month] += entry['count']

    summed_month_counts = [{'truncated_month': month, 'count': count} for month, count in summed_counts.items()]

    part_number_list = list(filtered_data.values_list("part_number_i_id", flat=True))
    technology_count_dict = defaultdict(int)
    for part_number in part_number_list:
        technology = PnMTMapping.objects.filter(part_number_i_id=part_number).values("technology_i_id").annotate(count=Count("technology_i_id")).order_by()
        for tech in technology:
            technology_count_dict[tech['technology_i_id']] += tech['count']
    technology_count = [{"technology_i_id": tech_id, "count": count} for tech_id, count in technology_count_dict.items()]

    line_counts = filtered_data.values("production_line_i_id").annotate(count=Count("production_line_i_id"))
    reason_counts = filtered_data.values("rejection_reason_i_id").annotate(count=Count("rejection_reason_i_id"))
    status_counts = filtered_data.values("part_status_i_id").annotate(count=Count("part_status_i_id"))

    date_list = [
        {"date": item["truncated_date"].strftime("%Y-%m-%d"), "count": item["count"]}
        for item in formatted_date_counts
    ]
    month_list = [
        {"month": item["truncated_month"].strftime("%Y-%m"), "count": item["count"]}
        for item in summed_month_counts
    ]
    technology_list = [{"technology_i_id": item["technology_i_id"], "count": item["count"]} for item in technology_count]
    line_list = [{"production_line_i_id": item["production_line_i_id"], "count": item["count"]} for item in line_counts]
    reason_list = [
        {"rejection_reason_i_id": item["rejection_reason_i_id"], "count": item["count"]} for item in reason_counts
    ]
    status_list = [
        {"part_status_i_id": item["part_status_i_id"], "count": item["count"]} for item in status_counts
    ]

    technology_codes = [item["technology_i_id"] for item in technology_list]
    technology_names = Icodes.objects.filter(Q(icode__in=technology_codes)).values(
        "icode", "name"
    )
    technology_mapping = {item["icode"]: item["name"] for item in technology_names}

    line_codes = [item["production_line_i_id"] for item in line_list]
    line_names = Icodes.objects.filter(Q(icode__in=line_codes)).values("icode", "name")
    line_mapping = {item["icode"]: item["name"] for item in line_names}

    reason_codes = [item["rejection_reason_i_id"] for item in reason_list]
    reason_names = Icodes.objects.filter(Q(icode__in=reason_codes)).values(
        "icode", "name"
    )
    reason_mapping = {item["icode"]: item["name"] for item in reason_names}

    status_codes = [item["part_status_i_id"] for item in status_list]
    status_names = Icodes.objects.filter(Q(icode__in=status_codes)).values(
        "icode", "name"
    )
    status_mapping = {item["icode"]: item["name"] for item in status_names}

    technology_with_names = sorted(
        [
            {
                "technology_i_id": item["technology_i_id"],
                "name": technology_mapping.get(item["technology_i_id"], item["technology_i_id"]),
                "count": item["count"],
            }
            for item in technology_list
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    line_with_names = sorted(
        [
            {
                "production_line_i_id": item["production_line_i_id"],
                "name": line_mapping.get(item["production_line_i_id"], item["production_line_i_id"]),
                "count": item["count"],
            }
            for item in line_list
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    reason_with_names = sorted(
        [
            {
                "rejection_reason_i_id": item["rejection_reason_i_id"],
                "name": reason_mapping.get(item["rejection_reason_i_id"], item["rejection_reason_i_id"]),
                "count": item["count"],
            }
            for item in reason_list
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    status_with_names = sorted(
        [
            {
                "part_status_i_id": item["part_status_i_id"],
                "name": status_mapping.get(item["part_status_i_id"], item["part_status_i_id"]),
                "count": item["count"],
            }
            for item in status_list
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    response_data = {
        "day_counts": date_list,
        "month_counts": month_list,
        "technology_counts": technology_with_names,
        "line_counts": line_with_names,
        "reason_counts": reason_with_names,
        "status_counts": status_with_names,
        "shift_counts": sel_shift_data,
    }
    return JsonResponse(response_data)
