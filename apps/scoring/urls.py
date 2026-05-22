from django.urls import path
from . import views

app_name = 'scoring'

urlpatterns = [
    # Judging dashboard
    path('', views.judging_dashboard_view, name='dashboard'),

    # Scoring
    path('competition/<uuid:competition_pk>/', views.competition_scoring_view, name='competition_scoring'),
    path('entry/<uuid:entry_pk>/', views.entry_scoring_view, name='entry_scoring'),
    path('entry/<uuid:entry_pk>/score-details/', views.entry_score_details_view, name='score_details'),
    path('entry/<uuid:entry_pk>/criteria/<uuid:criteria_pk>/', views.score_criteria_view, name='score_criteria'),
    path('my-scores/<uuid:competition_pk>/', views.my_scores_view, name='my_scores'),

    # Leaderboard
    path('leaderboard/<uuid:competition_pk>/', views.leaderboard_view, name='leaderboard'),
    path('leaderboard/<uuid:competition_pk>/export/', views.leaderboard_export_csv_view, name='leaderboard_export'),
]
