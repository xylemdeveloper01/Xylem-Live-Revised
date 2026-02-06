from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
import datetime

import xylem.custom_messages.constants as custom_messages
from xylem_apps.a000_xylem_master.tests import user_passes_test_custom, view_eligibity_test
from xylem_apps.a000_xylem_master import serve

from .forms import EventAdditionForm
from .models import EventData

	  										
@login_required(login_url="/accounts/login/")
def authenticated_index(request):  
    min_time_period = datetime.datetime.now() - datetime.timedelta(days=30) 
    events = EventData.objects.filter(added_datetime__gte=min_time_period).order_by('-added_datetime')[:10]
    context = {
        "segment": "index",
        "events": events
    }
    return render(request, "a008/authenticated_index.html", context)


@login_required(login_url="/accounts/login/")
@user_passes_test_custom(view_eligibity_test, depts_with_min_designation_as_list=([serve.PlantLocations.SP_Koil, serve.Depts.All_depts, serve.Designations.Deputy_Engineer_or_Executive],
																	   [serve.PlantLocations.SP_Koil, serve.Depts.Development_team, serve.Designations.All_designations],
																	   [serve.PlantLocations.All_plant_locations, serve.Depts.Business_administration, serve.Designations.President]), redirect_url="user_access_denied")
def event_addition(request):
    if request.method == 'POST':
        form = EventAdditionForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user           
            # Check if the current user has already added 3 events within the last 24 hours
            num_events_added_today = EventData.objects.filter(
                added_user=user, added_datetime__date=datetime.datetime.now().date()
            ).count()
            
            if num_events_added_today >= serve.max_number_of_events_added_a008:
                messages.add_message(request, custom_messages.DANGER_MODAL_MESSAGE, "You have already added the maximum number of events for today")
                return redirect("a008:home_schemer") 
                
            # Proceed with event addition if the user hasn't reached the limit
            caption = form.cleaned_data["caption"]
            description = form.cleaned_data["description"]
            event_image = form.cleaned_data["event_image"]
            EventData.objects.create(
                event_image=event_image,
                caption=caption,
                description=description,
                added_user=user
            )
            messages.add_message(request, custom_messages.SUCCESS_MODAL_MESSAGE, "Event added succcessfully")
            return redirect("a008:home_schemer")
    else:
        form = EventAdditionForm()
    context = {
        "segment": "Event addition",
        "form": form,
}   
    return render(request, "a008/event_addition.html", context)

