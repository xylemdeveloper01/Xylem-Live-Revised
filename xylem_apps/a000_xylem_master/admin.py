from django.contrib import admin

# Register your models here.

from .models import UserProfile, UserExtraFields, Icodes

admin.site.register(UserProfile)
admin.site.register(UserExtraFields)
admin.site.register(Icodes)
