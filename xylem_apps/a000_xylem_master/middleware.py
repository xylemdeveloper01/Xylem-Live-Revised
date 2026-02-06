import logging
from django.shortcuts import render

from .utils import set_current_user
from . import serve

a000_logger = logging.getLogger(serve.an_xylem_master)


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            set_current_user(request.user)
        else:
            set_current_user(None)
        return response 