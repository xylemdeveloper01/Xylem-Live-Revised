from functools import wraps
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import resolve_url
from django.contrib.auth.views import redirect_to_login

from django.test import TestCase
from . import serve


# Create your tests here.

def user_passes_test_custom(
    test_func, depts_with_min_designation_as_list, redirect_url=None, redirect_field_name=REDIRECT_FIELD_NAME
):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_view(request, *args, **kwargs):
            access_flag=None
            for i in depts_with_min_designation_as_list:
                if test_func(request.user, plant_location=i[0], dept=i[1], min_designation=i[2]):
                    access_flag=True
                    break
            if access_flag:
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(redirect_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if (not login_scheme or login_scheme == current_scheme) and (
                not login_netloc or login_netloc == current_netloc
            ):
                path = request.get_full_path()

            return redirect_to_login(path, resolved_login_url, redirect_field_name)

        return _wrapper_view

    return decorator

# user_passes_test_with_one_of_given_list
def user_passes_test_custom_not_as_decorator(user, depts_with_min_designation_as_list):
    for i in depts_with_min_designation_as_list:
        if view_eligibity_test(user, plant_location=i[0], dept=i[1], min_designation=i[2]):
            return True
    return False


def view_eligibity_test(user, plant_location, dept, min_designation):
    return ((plant_location == serve.PlantLocations.All_plant_locations or plant_location == user.plant_location_i) and
            (dept == serve.Depts.All_depts or dept ==  user.dept_i) and
            (min_designation == serve.Designations.All_designations or min_designation.icode <= user.designation_i.icode) )