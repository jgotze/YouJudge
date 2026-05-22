from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScoreViewSet, LeaderboardViewSet, JudgeProgressViewSet

router = DefaultRouter()
router.register(r'scores', ScoreViewSet, basename='score')
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')
router.register(r'progress', JudgeProgressViewSet, basename='judge-progress')

urlpatterns = [
    path('', include(router.urls)),
]
