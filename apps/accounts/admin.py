from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, EmailVerificationToken, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'email_verified', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'email_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'organization']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'bio', 'avatar', 'phone', 'organization')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'email_verified', 'groups', 'user_permissions'),
        }),
        (_('Preferences'), {'fields': ('email_notifications',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ['date_joined', 'last_login']


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin interface for EmailVerificationToken model."""

    list_display = ['user', 'token', 'created_at', 'expires_at', 'is_valid']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at']

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin interface for PasswordResetToken model."""

    list_display = ['user', 'token', 'created_at', 'expires_at', 'used', 'is_valid']
    list_filter = ['created_at', 'expires_at', 'used']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at']

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'
