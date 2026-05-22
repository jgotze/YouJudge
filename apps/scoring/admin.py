from django.contrib import admin
from .models import Score, Leaderboard, JudgeProgress


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    """Admin interface for Score model."""

    list_display = ['judge', 'entry', 'criteria', 'score_value', 'weighted_score', 'created_at']
    list_filter = ['score_value', 'created_at', 'criteria__competition']
    search_fields = ['judge__email', 'entry__title', 'criteria__title']
    readonly_fields = ['weighted_score', 'created_at', 'updated_at']

    fieldsets = (
        ('Score Information', {
            'fields': ('judge', 'entry', 'criteria', 'score_value', 'weighted_score')
        }),
        ('Additional Info', {
            'fields': ('comment',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """Admin interface for Leaderboard model."""

    list_display = ['competition', 'entry', 'rank', 'total_weighted_score', 'last_updated']
    list_filter = ['competition', 'last_updated']
    search_fields = ['entry__title', 'competition__title']
    readonly_fields = ['last_updated']

    fieldsets = (
        (None, {
            'fields': ('competition', 'entry', 'rank', 'total_weighted_score')
        }),
        ('Metadata', {
            'fields': ('last_updated',)
        }),
    )


@admin.register(JudgeProgress)
class JudgeProgressAdmin(admin.ModelAdmin):
    """Admin interface for JudgeProgress model."""

    list_display = ['judge', 'competition', 'scored_entries', 'total_entries', 'progress_percentage', 'last_scored_at']
    list_filter = ['competition', 'last_scored_at', 'updated_at']
    search_fields = ['judge__email', 'competition__title']
    readonly_fields = ['last_scored_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('judge', 'competition')
        }),
        ('Progress', {
            'fields': ('total_entries', 'scored_entries', 'progress_percentage')
        }),
        ('Metadata', {
            'fields': ('last_scored_at', 'updated_at')
        }),
    )
