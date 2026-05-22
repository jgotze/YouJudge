from rest_framework import serializers
from apps.competitions.models import Competition, JudgeAssignment, Criteria, Entry
from apps.accounts.api.serializers import UserSerializer


class CriteriaSerializer(serializers.ModelSerializer):
    """Serializer for Criteria model."""

    class Meta:
        model = Criteria
        fields = ['id', 'competition', 'title', 'description', 'weight', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class EntrySerializer(serializers.ModelSerializer):
    """Serializer for Entry model."""

    submitted_by = UserSerializer(read_only=True)
    total_score = serializers.ReadOnlyField()
    average_score = serializers.ReadOnlyField()

    class Meta:
        model = Entry
        fields = [
            'id', 'competition', 'title', 'participant_name', 'participant_email',
            'description', 'file', 'image', 'video_url', 'submitted_by',
            'submitted_at', 'updated_at', 'total_score', 'average_score'
        ]
        read_only_fields = ['id', 'submitted_by', 'submitted_at', 'updated_at']


class JudgeAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for JudgeAssignment model."""

    judge = UserSerializer(read_only=True)
    judge_email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = JudgeAssignment
        fields = [
            'id', 'competition', 'judge', 'judge_email', 'status',
            'invited_at', 'responded_at'
        ]
        read_only_fields = ['id', 'judge', 'invited_at', 'responded_at']


class CompetitionSerializer(serializers.ModelSerializer):
    """Serializer for Competition model."""

    created_by = UserSerializer(read_only=True)
    criteria = CriteriaSerializer(many=True, read_only=True)
    entries = EntrySerializer(many=True, read_only=True)
    judge_assignments = JudgeAssignmentSerializer(many=True, read_only=True)
    is_active = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    is_ended = serializers.ReadOnlyField()
    total_entries = serializers.ReadOnlyField()
    total_judges = serializers.ReadOnlyField()

    class Meta:
        model = Competition
        fields = [
            'id', 'title', 'description', 'created_by', 'start_date', 'end_date',
            'created_at', 'updated_at', 'status', 'icon', 'icon_color', 'rules',
            'max_entries_per_participant', 'criteria', 'entries', 'judge_assignments',
            'is_active', 'is_upcoming', 'is_ended', 'total_entries', 'total_judges'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class CompetitionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Competition list."""

    created_by = UserSerializer(read_only=True)
    total_entries = serializers.ReadOnlyField()
    total_judges = serializers.ReadOnlyField()

    class Meta:
        model = Competition
        fields = [
            'id', 'title', 'description', 'created_by', 'start_date', 'end_date',
            'status', 'icon', 'icon_color', 'total_entries', 'total_judges', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
