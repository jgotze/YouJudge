from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum, Avg
from django.http import HttpResponse, JsonResponse
import csv
from apps.competitions.models import Competition, JudgeAssignment, Entry, Criteria
from .models import Score, Leaderboard, JudgeProgress
from .forms import BulkScoreForm


@login_required
def judging_dashboard_view(request):
    """Display judge's dashboard with assigned competitions."""
    assignments = JudgeAssignment.objects.filter(
        judge=request.user,
        status='accepted'
    ).select_related('competition').order_by('-invited_at')

    # Get progress for each competition
    progress_data = []
    for assignment in assignments:
        progress = JudgeProgress.update_progress(request.user, assignment.competition)
        progress_data.append({
            'assignment': assignment,
            'progress': progress,
        })

    context = {
        'progress_data': progress_data,
    }
    return render(request, 'scoring/judging_dashboard.html', context)


@login_required
def competition_scoring_view(request, competition_pk):
    """Display flat entry×criteria rows for scoring."""
    competition = get_object_or_404(Competition, pk=competition_pk)
    competition.sync_status()

    if not competition.can_user_judge(request.user):
        raise PermissionDenied("You don't have permission to score this competition.")

    entries = competition.entries.select_related('category').order_by('category__name', 'title')
    criteria = competition.criteria.all().order_by('order')

    judge_scores = Score.objects.filter(
        judge=request.user,
        entry__competition=competition
    ).select_related('entry', 'criteria')

    scores_map = {(s.entry.id, s.criteria.id): s for s in judge_scores}

    rows = []
    for entry in entries:
        for criterion in criteria:
            rows.append({
                'entry': entry,
                'criteria': criterion,
                'score': scores_map.get((entry.id, criterion.id)),
            })

    from apps.competitions.models import Category
    categories = Category.objects.filter(competition=competition)

    context = {
        'competition': competition,
        'rows': rows,
        'score_range': range(competition.max_score + 1),
        'entries': entries,
        'criteria': criteria,
        'categories': categories,
        'scoring_is_open': competition.scoring_is_open,
    }
    return render(request, 'scoring/competition_scoring.html', context)


@login_required
def score_criteria_view(request, entry_pk, criteria_pk):
    """Save a score for one entry-criteria pair."""
    entry = get_object_or_404(Entry, pk=entry_pk)
    criterion = get_object_or_404(Criteria, pk=criteria_pk, competition=entry.competition)
    competition = entry.competition
    competition.sync_status()

    if not competition.can_user_judge(request.user):
        raise PermissionDenied("You don't have permission to score this entry.")

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not competition.scoring_is_open:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': 'Scoring is not open for this competition.'}, status=403)
        messages.error(request, 'Scoring is not open for this competition.')
        return redirect('scoring:competition_scoring', competition_pk=competition.pk)

    if request.method == 'POST':
        score_value = request.POST.get('score_value')
        if score_value is not None:
            try:
                value = int(score_value)
            except ValueError:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': 'Invalid score'}, status=400)
                return redirect('scoring:competition_scoring', competition_pk=entry.competition.pk)

            max_score = entry.competition.max_score
            if 0 <= value <= max_score:
                Score.all_objects.update_or_create(
                    judge=request.user,
                    entry=entry,
                    criteria=criterion,
                    defaults={'score_value': value, 'deleted_at': None},
                )
                JudgeProgress.update_progress(request.user, entry.competition)
                Leaderboard.update_leaderboard(entry.competition)
                if is_ajax:
                    return JsonResponse({'status': 'ok', 'score_value': value})
            elif is_ajax:
                return JsonResponse({'status': 'error', 'message': 'Score out of range'}, status=400)

    if is_ajax:
        return JsonResponse({'status': 'error'}, status=400)
    return redirect('scoring:competition_scoring', competition_pk=entry.competition.pk)


@login_required
def entry_scoring_view(request, entry_pk):
    """Score a specific entry."""
    entry = get_object_or_404(Entry, pk=entry_pk)
    competition = entry.competition
    competition.sync_status()

    # Check if user is an accepted judge
    if not competition.can_user_judge(request.user):
        raise PermissionDenied("You don't have permission to score this entry.")

    if not competition.scoring_is_open:
        messages.error(request, 'Scoring is not open for this competition.')
        return redirect('scoring:competition_scoring', competition_pk=competition.pk)

    if request.method == 'POST':
        form = BulkScoreForm(request.POST, entry=entry, judge=request.user)
        if form.is_valid():
            # Save scores for each criteria
            for criteria in competition.criteria.all():
                score_value = form.cleaned_data.get(f'score_{criteria.id}')
                comment = form.cleaned_data.get(f'comment_{criteria.id}', '')

                # Update or create score
                Score.all_objects.update_or_create(
                    judge=request.user,
                    entry=entry,
                    criteria=criteria,
                    defaults={
                        'score_value': score_value,
                        'comment': comment,
                        'deleted_at': None,
                    }
                )

            # Update judge progress
            JudgeProgress.update_progress(request.user, competition)

            # Update leaderboard
            Leaderboard.update_leaderboard(competition)

            messages.success(request, f'Scores saved for "{entry.title}"!')
            return redirect('scoring:competition_scoring', competition_pk=competition.pk)
    else:
        form = BulkScoreForm(entry=entry, judge=request.user)

    # Get existing scores
    existing_scores = Score.objects.filter(
        judge=request.user,
        entry=entry
    ).select_related('criteria')

    context = {
        'entry': entry,
        'competition': competition,
        'form': form,
        'existing_scores': existing_scores,
    }
    return render(request, 'scoring/entry_scoring.html', context)


@login_required
def leaderboard_view(request, competition_pk):
    """Display competition leaderboard."""
    competition = get_object_or_404(Competition, pk=competition_pk)

    # Check permissions
    is_owner = competition.created_by == request.user
    is_judge = competition.can_user_judge(request.user)

    if not (is_owner or is_judge):
        raise PermissionDenied("You don't have permission to view this leaderboard.")

    # Update leaderboard
    Leaderboard.update_leaderboard(competition)

    # Get leaderboard entries
    leaderboard_entries = Leaderboard.objects.filter(
        competition=competition
    ).select_related('entry').order_by('rank')

    # Get detailed scoring breakdown
    entries_with_scores = []
    for leaderboard_entry in leaderboard_entries:
        entry = leaderboard_entry.entry

        # Get scores by judge
        judge_scores = Score.objects.filter(entry=entry).select_related('judge', 'criteria')

        # Calculate average score per criteria
        criteria_averages = {}
        for criteria in competition.criteria.all():
            scores = Score.objects.filter(entry=entry, criteria=criteria)
            if scores.exists():
                avg = scores.aggregate(Avg('score_value'))['score_value__avg']
                criteria_averages[criteria.id] = round(avg, 2) if avg else 0
            else:
                criteria_averages[criteria.id] = 0

        entries_with_scores.append({
            'leaderboard_entry': leaderboard_entry,
            'entry': entry,
            'judge_scores': judge_scores,
            'criteria_averages': criteria_averages,
        })

    context = {
        'competition': competition,
        'entries_with_scores': entries_with_scores,
        'criteria': competition.criteria.all(),
        'is_owner': is_owner,
        'is_judge': is_judge,
    }
    return render(request, 'scoring/leaderboard.html', context)


@login_required
def entry_score_details_view(request, entry_pk):
    """Show detailed per-judge, per-criterion score breakdown for a single entry."""
    entry = get_object_or_404(Entry, pk=entry_pk)
    competition = entry.competition

    is_owner = competition.created_by == request.user
    is_judge = competition.can_user_judge(request.user)

    if not (is_owner or is_judge):
        raise PermissionDenied("You don't have permission to view score details.")

    criteria = competition.criteria.all().order_by('order')
    max_score = competition.max_score

    criteria_breakdown = []
    for criterion in criteria:
        scores = Score.objects.filter(
            entry=entry,
            criteria=criterion
        ).select_related('judge').order_by('judge__first_name', 'judge__email')

        avg = scores.aggregate(Avg('score_value'))['score_value__avg']
        avg_rounded = round(avg, 2) if avg else None
        weighted_contribution = round(avg * criterion.weight, 3) if avg else 0

        criteria_breakdown.append({
            'criterion': criterion,
            'scores': scores,
            'average': avg_rounded,
            'weighted_contribution': weighted_contribution,
        })

    leaderboard_entry = Leaderboard.objects.filter(
        competition=competition,
        entry=entry
    ).first()

    context = {
        'entry': entry,
        'competition': competition,
        'criteria_breakdown': criteria_breakdown,
        'leaderboard_entry': leaderboard_entry,
        'max_score': max_score,
        'is_owner': is_owner,
    }
    return render(request, 'scoring/score_details.html', context)


@login_required
def leaderboard_export_csv_view(request, competition_pk):
    """Export leaderboard as CSV."""
    competition = get_object_or_404(Competition, pk=competition_pk)

    # Check permissions
    if not (competition.created_by == request.user or competition.can_user_judge(request.user)):
        raise PermissionDenied("You don't have permission to export this leaderboard.")

    # Update leaderboard
    Leaderboard.update_leaderboard(competition)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{competition.title}_leaderboard.csv"'

    writer = csv.writer(response)

    # Header
    header = ['Rank', 'Entry Title', 'Participant', 'Total Score']
    for criteria in competition.criteria.all():
        header.append(f'{criteria.title} (Avg)')
    writer.writerow(header)

    # Data rows
    leaderboard_entries = Leaderboard.objects.filter(
        competition=competition
    ).select_related('entry').order_by('rank')

    for leaderboard_entry in leaderboard_entries:
        entry = leaderboard_entry.entry
        row = [
            leaderboard_entry.rank,
            entry.title,
            entry.participant_name,
            leaderboard_entry.total_weighted_score,
        ]

        # Add average scores for each criteria
        for criteria in competition.criteria.all():
            scores = Score.objects.filter(entry=entry, criteria=criteria)
            if scores.exists():
                avg = scores.aggregate(Avg('score_value'))['score_value__avg']
                row.append(round(avg, 2) if avg else 0)
            else:
                row.append(0)

        writer.writerow(row)

    return response


@login_required
def my_scores_view(request, competition_pk):
    """Display judge's own scores for a competition."""
    competition = get_object_or_404(Competition, pk=competition_pk)

    # Check if user is an accepted judge
    if not competition.can_user_judge(request.user):
        raise PermissionDenied("You don't have permission to view scores for this competition.")

    # Get all scores by this judge
    scores = Score.objects.filter(
        judge=request.user,
        entry__competition=competition
    ).select_related('entry', 'criteria').order_by('entry__title', 'criteria__order')

    # Group scores by entry
    entries_scores = {}
    for score in scores:
        entry_id = score.entry.id
        if entry_id not in entries_scores:
            entries_scores[entry_id] = {
                'entry': score.entry,
                'scores': []
            }
        entries_scores[entry_id]['scores'].append(score)

    context = {
        'competition': competition,
        'entries_scores': entries_scores.values(),
    }
    return render(request, 'scoring/my_scores.html', context)
