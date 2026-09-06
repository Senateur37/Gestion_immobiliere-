from django.contrib import admin

from .models import Payment, PaymentAllocation, RentCharge


class AllocationInline(admin.TabularInline):
    model = PaymentAllocation
    extra = 0
    readonly_fields = ['created_at']


@admin.register(RentCharge)
class RentChargeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'lease', 'due_date', 'amount_due', 'status', 'organization']
    list_filter = ['status', 'kind', 'organization']
    date_hierarchy = 'due_date'
    search_fields = ['label', 'lease__lease_number']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference', 'lease', 'amount', 'payment_date', 'method', 'organization']
    list_filter = ['method', 'organization']
    date_hierarchy = 'payment_date'
    search_fields = ['reference', 'external_reference', 'lease__lease_number']
    inlines = [AllocationInline]
