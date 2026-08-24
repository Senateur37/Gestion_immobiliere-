from django.contrib import admin

from .models import MaintenanceAttachment, MaintenanceRequest

admin.site.register(MaintenanceRequest)
admin.site.register(MaintenanceAttachment)
