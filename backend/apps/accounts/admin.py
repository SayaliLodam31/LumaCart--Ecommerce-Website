from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_staff', 'is_active', 'is_email_verified')
    list_filter = ('is_staff', 'is_active', 'is_email_verified', 'groups')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password', 'is_staff', 'is_active'),
        }),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'state', 'postal_code', 'is_default', 'address_type')
    list_filter = ('is_default', 'address_type', 'city', 'country')
    search_fields = ('full_name', 'street_address', 'city', 'postal_code', 'user__email')
