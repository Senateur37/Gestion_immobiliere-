from django.contrib import admin

from .models import Property, PropertyImage, Unit


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
	list_display = ('name', 'city', 'property_type', 'owner', 'is_active')
	list_filter = ('property_type', 'is_active', 'city')
	search_fields = ('name', 'address', 'city')


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
	list_display = ('property', 'unit_number', 'rent_amount', 'status')
	list_filter = ('status',)
	search_fields = ('property__name', 'unit_number')


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
	list_display = ('property', 'unit', 'is_primary', 'display_order')
