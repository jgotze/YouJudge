from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from apps.competitions.models import Competition, JudgeAssignment, Criteria, Entry
from .serializers import (
    CompetitionSerializer, CompetitionListSerializer,
    JudgeAssignmentSerializer, CriteriaSerializer, EntrySerializer
)
from .permissions import IsCompetitionOwnerOrReadOnly, IsJudgeOrOwner

User = get_user_model()


class CompetitionViewSet(viewsets.ModelViewSet):
    """ViewSet for Competition model."""

    queryset = Competition.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsCompetitionOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'created_by']

    def get_serializer_class(self):
        if self.action == 'list':
            return CompetitionListSerializer
        return CompetitionSerializer

    def get_queryset(self):
        user = self.request.user
        # Return competitions created by user or where user is a judge
        return Competition.objects.filter(
            models.Q(created_by=user) |
            models.Q(judge_assignments__judge=user, judge_assignments__status='accepted')
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a competition."""
        competition = self.get_object()

        if competition.status != 'draft':
            return Response(
                {'error': 'Only draft competitions can be activated.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        competition.status = 'active'
        competition.save()

        return Response({'message': 'Competition activated successfully.'})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a competition."""
        competition = self.get_object()

        competition.status = 'closed'
        competition.save()

        return Response({'message': 'Competition closed successfully.'})


class JudgeAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for JudgeAssignment model."""

    queryset = JudgeAssignment.objects.all()
    serializer_class = JudgeAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['competition', 'judge', 'status']

    def get_queryset(self):
        user = self.request.user
        # Return assignments where user is the judge or competition owner
        return JudgeAssignment.objects.filter(
            models.Q(judge=user) |
            models.Q(competition__created_by=user)
        ).distinct()

    def create(self, request, *args, **kwargs):
        """Create a new judge assignment."""
        competition_id = request.data.get('competition')
        judge_email = request.data.get('judge_email')

        try:
            competition = Competition.objects.get(id=competition_id)

            if competition.created_by != request.user:
                return Response(
                    {'error': 'Only competition owner can invite judges.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            judge = User.objects.get(email=judge_email)

            if JudgeAssignment.objects.filter(competition=competition, judge=judge).exists():
                return Response(
                    {'error': 'Judge already assigned to this competition.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            assignment = JudgeAssignment.objects.create(
                competition=competition,
                judge=judge,
                status='invited'
            )

            serializer = self.get_serializer(assignment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Competition.DoesNotExist:
            return Response(
                {'error': 'Competition not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found with this email.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept judge assignment."""
        assignment = self.get_object()

        if assignment.judge != request.user:
            return Response(
                {'error': 'You can only accept your own invitations.'},
                status=status.HTTP_403_FORBIDDEN
            )

        assignment.accept()

        return Response({'message': 'Assignment accepted successfully.'})

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline judge assignment."""
        assignment = self.get_object()

        if assignment.judge != request.user:
            return Response(
                {'error': 'You can only decline your own invitations.'},
                status=status.HTTP_403_FORBIDDEN
            )

        assignment.decline()

        return Response({'message': 'Assignment declined.'})


class CriteriaViewSet(viewsets.ModelViewSet):
    """ViewSet for Criteria model."""

    queryset = Criteria.objects.all()
    serializer_class = CriteriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['competition']

    def get_queryset(self):
        user = self.request.user
        # Return criteria for competitions user owns or judges
        return Criteria.objects.filter(
            models.Q(competition__created_by=user) |
            models.Q(competition__judge_assignments__judge=user, competition__judge_assignments__status='accepted')
        ).distinct()


class EntryViewSet(viewsets.ModelViewSet):
    """ViewSet for Entry model."""

    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['competition']

    def get_queryset(self):
        user = self.request.user
        # Return entries for competitions user owns or judges
        return Entry.objects.filter(
            models.Q(competition__created_by=user) |
            models.Q(competition__judge_assignments__judge=user, competition__judge_assignments__status='accepted')
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)
