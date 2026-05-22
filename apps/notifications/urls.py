from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_list_view, name='list'),
    path('<uuid:pk>/read/', views.notification_mark_read_view, name='mark_read'),
    path('mark-all-read/', views.notifications_mark_all_read_view, name='mark_all_read'),
    path('api/unread-count/', views.notifications_unread_count_view, name='unread_count'),
]
