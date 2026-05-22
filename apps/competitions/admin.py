from django.contrib import admin
from .models import Competition, JudgeAssignment, Criteria, Entry


class CriteriaInline(admin.TabularInline):
    """Inline admin for criteria."""
    model = Criteria
    extra = 1
    fields = ['title', 'description', 'weight', 'order']


class JudgeAssignmentInline(admin.TabularInline):
    """Inline admin for judge assignments."""
    model = JudgeAssignment
    extra = 1
    fields = ['judge', 'status', 'invited_at', 'responded_at']
    readonly_fields = ['invited_at', 'responded_at']


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    """Admin interface for Competition model."""

    list_display = ['title', 'created_by', 'status', 'start_date', 'end_date', 'total_entries', 'total_judges']
    list_filter = ['status', 'start_date', 'end_date', 'created_at']
    search_fields = ['title', 'description', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CriteriaInline, JudgeAssignmentInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'created_by', 'image')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Settings', {
            'fields': ('rules', 'max_entries_per_participant')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JudgeAssignment)
class JudgeAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for JudgeAssignment model."""

    list_display = ['competition', 'judge', 'status', 'invited_at', 'responded_at']
    list_filter = ['status', 'invited_at', 'responded_at']
    search_fields = ['competition__title', 'judge__email']
    readonly_fields = ['invited_at', 'responded_at']

    fieldsets = (
        (None, {
            'fields': ('competition', 'judge', 'status')
        }),
        ('Timestamps', {
            'fields': ('invited_at', 'responded_at')
        }),
    )


@admin.register(Criteria)
class CriteriaAdmin(admin.ModelAdmin):
    """Admin interface for Criteria model."""

    list_display = ['title', 'competition', 'weight', 'order', 'created_at']
    list_filter = ['weight', 'created_at']
    search_fields = ['title', 'description', 'competition__title']
    readonly_fields = ['created_at']

    fieldsets = (
        (None, {
            'fields': ('competition', 'title', 'description')
        }),
        ('Settings', {
            'fields': ('weight', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    """Admin interface for Entry model."""

    list_display = ['title', 'participant_name', 'competition', 'submitted_at', 'total_score']
    list_filter = ['competition', 'submitted_at']
    search_fields = ['title', 'participant_name', 'participant_email', 'description']
    readonly_fields = ['submitted_at', 'updated_at', 'total_score']

    fieldsets = (
        ('Entry Information', {
            'fields': ('competition', 'title', 'description')
        }),
        ('Participant', {
            'fields': ('participant_name', 'participant_email', 'submitted_by')
        }),
        ('Attachments', {
            'fields': ('file', 'image', 'video_url')
        }),
        ('Metadata', {
            'fields': ('submitted_at', 'updated_at', 'total_score'),
            'classes': ('collapse',)
        }),
    )
