from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'full_name',
        'is_private',
        'is_email_verified',
        'is_active',
        'is_staff',
        'date_joined',
    )
    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        'is_private',
        'is_email_verified',
        'date_joined',
    )
    search_fields = ('username', 'email', 'full_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profile Information', {
            'fields': (
                'username',
                'full_name',
                'profile_picture',
                'bio',
                'website',
                'location',
            )
        }),
        ('Privacy & Verification', {
            'fields': ('is_private', 'is_email_verified')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined', 'updated_at')}),
    )

    readonly_fields = ('date_joined', 'updated_at', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'full_name',
                'password1',
                'password2',
                'is_staff',
                'is_superuser',
            ),
        }),
    )
