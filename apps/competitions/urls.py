from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    path('my-judges/', views.my_judges_view, name='my_judges'),

    # Competition CRUD
    path('create/', views.competition_create_view, name='create'),
    path('<uuid:pk>/', views.competition_detail_view, name='detail'),
    path('<uuid:pk>/edit/', views.competition_edit_view, name='edit'),
    path('<uuid:pk>/delete/', views.competition_delete_view, name='delete'),
    path('<uuid:pk>/status/', views.competition_status_update_view, name='update_status'),

    # Judge management
    path('<uuid:pk>/judges/invite/', views.judge_invite_view, name='judge_invite'),
    path('<uuid:pk>/judges/add-self/', views.judge_add_self_view, name='judge_add_self'),
    path('judges/<uuid:pk>/<str:action>/', views.judge_assignment_respond_view, name='judge_respond'),
    path('judges/<uuid:pk>/remove/', views.judge_remove_view, name='judge_remove'),

    # Criteria management
    path('<uuid:competition_pk>/criteria/create/', views.criteria_create_view, name='criteria_create'),
    path('criteria/<uuid:pk>/edit/', views.criteria_edit_view, name='criteria_edit'),
    path('criteria/<uuid:pk>/delete/', views.criteria_delete_view, name='criteria_delete'),

    # Entry management
    path('<uuid:competition_pk>/entries/create/', views.entry_create_view, name='entry_create'),
    path('entries/<uuid:pk>/edit/', views.entry_edit_view, name='entry_edit'),
    path('entries/<uuid:pk>/delete/', views.entry_delete_view, name='entry_delete'),

    # Category management
    path('<uuid:competition_pk>/categories/create/', views.category_create_view, name='category_create'),
    path('categories/<uuid:pk>/delete/', views.category_delete_view, name='category_delete'),
]
