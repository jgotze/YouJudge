from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompetitionViewSet, JudgeAssignmentViewSet, CriteriaViewSet, EntryViewSet

router = DefaultRouter()
router.register(r'competitions', CompetitionViewSet, basename='competition')
router.register(r'judges', JudgeAssignmentViewSet, basename='judge-assignment')
router.register(r'criteria', CriteriaViewSet, basename='criteria')
router.register(r'entries', EntryViewSet, basename='entry')

urlpatterns = [
    path('', include(router.urls)),
]
