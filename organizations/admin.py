from django.contrib import admin

from .models import Membership, Organization


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = ['user']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'kind', 'currency', 'country', 'is_active', 'created_at']
    list_filter = ['kind', 'is_active', 'country']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_default', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['user__username', 'user__email', 'organization__name']
    autocomplete_fields = ['user', 'organization']
