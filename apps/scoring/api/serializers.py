from rest_framework import serializers
from apps.scoring.models import Score, Leaderboard, JudgeProgress
from apps.accounts.api.serializers import UserSerializer
from apps.competitions.api.serializers import EntrySerializer, CriteriaSerializer


class ScoreSerializer(serializers.ModelSerializer):
    """Serializer for Score model."""

    judge = UserSerializer(read_only=True)
    entry = EntrySerializer(read_only=True)
    criteria = CriteriaSerializer(read_only=True)

    entry_id = serializers.UUIDField(write_only=True)
    criteria_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Score
        fields = [
            'id', 'judge', 'entry', 'criteria', 'entry_id', 'criteria_id',
            'score_value', 'weighted_score', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'judge', 'weighted_score', 'created_at', 'updated_at']


class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for Leaderboard model."""

    entry = EntrySerializer(read_only=True)

    class Meta:
        model = Leaderboard
        fields = ['id', 'competition', 'entry', 'total_weighted_score', 'rank', 'last_updated']
        read_only_fields = ['id', 'total_weighted_score', 'rank', 'last_updated']


class JudgeProgressSerializer(serializers.ModelSerializer):
    """Serializer for JudgeProgress model."""

    judge = UserSerializer(read_only=True)

    class Meta:
        model = JudgeProgress
        fields = [
            'id', 'judge', 'competition', 'total_entries', 'scored_entries',
            'progress_percentage', 'last_scored_at', 'updated_at'
        ]
        read_only_fields = ['id', 'judge', 'total_entries', 'scored_entries', 'progress_percentage', 'last_scored_at', 'updated_at']
