"""
URL configuration for xylem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from xylem_apps.a000_xylem_master import serve

from . import views

app_name = serve.an_tools_management_system
urlpatterns = [
    path('projects/tool_cards/<int:current_product_category_id>/<int:current_tool_type_id>', views.tool_cards, name='tool_cards'),
    path('projects/tool_cards/tool_life_boost/<int:tool_type_id>/<int:tps_map_id>', views.tool_life_boost, name='tool_life_boost'),
    path('reports/tool_history_card/<int:current_product_category_id>/<int:current_tool_type_id>/', views.tool_history_card, name='tool_history_card'),

    path('ajax_tool_cards_of_tools_with_low_life/', views.ajax_tool_cards_of_tools_with_low_life, name='ajax_tool_cards_of_tools_with_low_life'),
    path('ajax_tool_cards_of_pl/', views.ajax_tool_cards_of_pl, name='ajax_tool_cards_of_pl'),  
    path('ajax_tool_cards_of_tool/', views.ajax_tool_cards_of_tool, name='ajax_tool_cards_of_tool'),
    path('ajax_tool_cards_of_tool/', views.ajax_tool_cards_of_tool, name='ajax_tool_cards_of_tool'),
    path('ajax_tool_history_card/',views.ajax_tool_history_card,name='ajax_tool_history_card'),
]
