from django.db import models
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.scoring.models import Score, Leaderboard, JudgeProgress
from apps.competitions.models import Entry, Criteria
from .serializers import ScoreSerializer, LeaderboardSerializer, JudgeProgressSerializer


class ScoreViewSet(viewsets.ModelViewSet):
    """ViewSet for Score model."""

    queryset = Score.objects.all()
    serializer_class = ScoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['entry', 'criteria', 'judge']

    def get_queryset(self):
        user = self.request.user
        # Return scores for competitions where user is a judge or owner
        return Score.objects.filter(
            models.Q(judge=user) |
            models.Q(entry__competition__created_by=user)
        ).distinct()

    def perform_create(self, serializer):
        """Create a score and update related models."""
        entry_id = serializer.validated_data.pop('entry_id')
        criteria_id = serializer.validated_data.pop('criteria_id')

        try:
            entry = Entry.objects.get(id=entry_id)
            criteria = Criteria.objects.get(id=criteria_id)

            # Check if user is an accepted judge
            if not entry.competition.can_user_judge(self.request.user):
                raise permissions.PermissionDenied("You are not authorized to score this entry.")

            # Create or update score
            score, created = Score.objects.update_or_create(
                judge=self.request.user,
                entry=entry,
                criteria=criteria,
                defaults={
                    'score_value': serializer.validated_data['score_value'],
                    'comment': serializer.validated_data.get('comment', ''),
                }
            )

            # Update judge progress
            JudgeProgress.update_progress(self.request.user, entry.competition)

            # Update leaderboard
            Leaderboard.update_leaderboard(entry.competition)

        except (Entry.DoesNotExist, Criteria.DoesNotExist):
            raise serializers.ValidationError("Entry or Criteria not found.")


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Leaderboard model."""

    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['competition']

    def get_queryset(self):
        user = self.request.user
        # Return leaderboard for competitions where user is a judge or owner
        return Leaderboard.objects.filter(
            models.Q(competition__created_by=user) |
            models.Q(competition__judge_assignments__judge=user, competition__judge_assignments__status='accepted')
        ).distinct()

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_leaderboard(self, request):
        """Update leaderboard for a competition."""
        competition_id = request.data.get('competition_id')

        if not competition_id:
            return Response(
                {'error': 'competition_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from apps.competitions.models import Competition
            competition = Competition.objects.get(id=competition_id)

            # Check permissions
            if not (competition.created_by == request.user or competition.can_user_judge(request.user)):
                return Response(
                    {'error': 'You do not have permission to update this leaderboard.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            Leaderboard.update_leaderboard(competition)

            leaderboard = Leaderboard.objects.filter(competition=competition)
            serializer = self.get_serializer(leaderboard, many=True)

            return Response(serializer.data)

        except Competition.DoesNotExist:
            return Response(
                {'error': 'Competition not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class JudgeProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for JudgeProgress model."""

    queryset = JudgeProgress.objects.all()
    serializer_class = JudgeProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['competition', 'judge']

    def get_queryset(self):
        user = self.request.user
        # Return progress for user's judging assignments or competitions they own
        return JudgeProgress.objects.filter(
            models.Q(judge=user) |
            models.Q(competition__created_by=user)
        ).distinct()
