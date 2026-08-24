from django.contrib import admin

from .models import Inspection, Lease, LeaseTenant

admin.site.register(Lease)
admin.site.register(LeaseTenant)
admin.site.register(Inspection)
