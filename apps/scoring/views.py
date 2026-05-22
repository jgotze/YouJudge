from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum, Avg
from django.http import HttpResponse, JsonResponse
import csv
import io
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter
from apps.competitions.models import Competition, JudgeAssignment, Entry, Criteria
from .models import Score, Leaderboard, JudgeProgress
from .forms import BulkScoreForm


@login_required
def judging_dashboard_view(request):
    assignments = JudgeAssignment.objects.filter(
        judge=request.user,
        status='accepted'
    ).select_related('competition').order_by('-invited_at')

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
    ).select_related('entry', 'entry__category').order_by('rank')

    criteria_qs = list(competition.criteria.all())

    # Build per-entry scoring detail and group by category
    from collections import OrderedDict
    categories = OrderedDict()  # category_name -> list of entry dicts

    for leaderboard_entry in leaderboard_entries:
        entry = leaderboard_entry.entry
        cat_name = entry.category.name if entry.category else "Uncategorised"

        judge_scores = Score.objects.filter(entry=entry).select_related('judge', 'criteria')

        criteria_averages = {}
        for criteria in criteria_qs:
            scores = Score.objects.filter(entry=entry, criteria=criteria)
            if scores.exists():
                avg = scores.aggregate(Avg('score_value'))['score_value__avg']
                criteria_averages[criteria.id] = round(avg, 2) if avg else 0
            else:
                criteria_averages[criteria.id] = 0

        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append({
            'leaderboard_entry': leaderboard_entry,
            'entry': entry,
            'judge_scores': judge_scores,
            'criteria_averages': criteria_averages,
        })

    # Re-rank within each category
    for cat_name, entries in categories.items():
        entries.sort(key=lambda d: d['leaderboard_entry'].total_weighted_score, reverse=True)
        for i, d in enumerate(entries, start=1):
            d['cat_rank'] = i

    context = {
        'competition': competition,
        'categories': categories,
        'criteria': criteria_qs,
        'is_owner': is_owner,
        'is_judge': is_judge,
        'multi_category': len(categories) > 1,
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
    from django.utils import timezone
    import re

    competition = get_object_or_404(Competition, pk=competition_pk)

    if not (competition.created_by == request.user or competition.can_user_judge(request.user)):
        raise PermissionDenied("You don't have permission to export this leaderboard.")

    Leaderboard.update_leaderboard(competition)

    safe_title = re.sub(r'[^\w\s-]', '', competition.title).strip().replace(' ', '_')
    export_date = timezone.now().strftime('%Y-%m-%d')
    filename = f"{safe_title}_leaderboard_{export_date}.xlsx"

    criteria_list = list(competition.criteria.all())
    judges_count = competition.judge_assignments.filter(status='accepted').count()

    leaderboard_entries = list(
        Leaderboard.objects.filter(competition=competition)
        .select_related('entry', 'entry__category')
        .order_by('rank')
    )

    # ── Colour palette ──────────────────────────────────────────────────────
    GOLD   = "FFD700"
    SILVER = "C0C0C0"
    BRONZE = "CD7F32"

    HDR_BG    = "1F3864"   # dark navy  – main column headers
    HDR_FG    = "FFFFFF"
    META_BG   = "2E75B6"   # mid blue   – metadata labels
    META_FG   = "FFFFFF"
    CRIT_BG   = "2F5496"   # accent blue – criteria sub-headers
    CRIT_FG   = "FFFFFF"
    ALT_ROW   = "EBF3FB"   # light blue  – alternating rows
    WHITE     = "FFFFFF"

    thin = Side(style='thin', color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def cell_style(ws, row, col, value, bold=False, bg=None, fg="000000",
                   align="left", wrap=False, num_fmt=None):
        c = ws.cell(row=row, column=col, value=value)
        c.font = Font(bold=bold, color=fg, name="Calibri", size=10)
        if bg:
            c.fill = PatternFill("solid", fgColor=bg)
        c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
        c.border = border
        if num_fmt:
            c.number_format = num_fmt
        return c

    # ── Workbook / sheets ────────────────────────────────────────────────────
    wb = Workbook()

    # ── Sheet 1: Leaderboard ─────────────────────────────────────────────────
    ws = wb.active
    ws.title = "Leaderboard"
    ws.freeze_panes = "A3"   # freeze first two rows

    # --- Metadata rows (col A=label, col B=value) ---
    meta = [
        ("Competition",          competition.title),
        ("Status",               competition.get_status_display()),
        ("Start Date",           competition.start_date.strftime('%Y-%m-%d %H:%M')),
        ("End Date",             competition.end_date.strftime('%Y-%m-%d %H:%M')),
        ("Max Score / Criteria", competition.max_score),
        ("Total Entries",        competition.entries.count()),
        ("Total Judges",         judges_count),
        ("Exported At",          timezone.now().strftime('%Y-%m-%d %H:%M')),
    ]

    # Title banner spanning full width
    total_cols = 8 + len(criteria_list) * 2
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    title_cell = ws.cell(row=1, column=1, value=f"  {competition.title} – Leaderboard Export")
    title_cell.font = Font(bold=True, color=HDR_FG, name="Calibri", size=14)
    title_cell.fill = PatternFill("solid", fgColor=HDR_BG)
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 28

    # Metadata block (rows 2–9)
    for i, (label, value) in enumerate(meta, start=2):
        cell_style(ws, i, 1, label, bold=True, bg=META_BG, fg=META_FG, align="right")
        cell_style(ws, i, 2, value, bg=WHITE, align="left")
        # merge value across a couple of columns for readability
        ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=4)

    meta_end_row = 1 + len(meta)

    # Gap row
    gap_row = meta_end_row + 1

    # --- Column headers ---
    header_row = gap_row + 1
    fixed_headers = [
        ("Rank",               "center"),
        ("Entry Title",        "left"),
        ("Category",           "left"),
        ("Participant Name",   "left"),
        ("Participant Email",  "left"),
        ("Submitted At",       "center"),
        ("Judges Scored",      "center"),
        ("Total Score",        "center"),
    ]
    for col, (label, align) in enumerate(fixed_headers, start=1):
        cell_style(ws, header_row, col, label, bold=True,
                   bg=HDR_BG, fg=HDR_FG, align=align)

    col = 9
    for c in criteria_list:
        label = f"{c.title}  (×{c.weight})"
        # Merge two columns for the criteria group header
        ws.merge_cells(start_row=header_row, start_column=col,
                       end_row=header_row, end_column=col + 1)
        cell_style(ws, header_row, col, label, bold=True,
                   bg=CRIT_BG, fg=CRIT_FG, align="center", wrap=True)
        col += 2

    # Sub-headers for criteria
    sub_row = header_row + 1
    for col in range(1, 9):
        cell_style(ws, sub_row, col, "", bg=HDR_BG)   # blank spacer

    col = 9
    for c in criteria_list:
        cell_style(ws, sub_row, col,     f"Avg /{competition.max_score}",
                   bold=True, bg=CRIT_BG, fg=CRIT_FG, align="center")
        cell_style(ws, sub_row, col + 1, "# Judges",
                   bold=True, bg=CRIT_BG, fg=CRIT_FG, align="center")
        col += 2

    ws.row_dimensions[header_row].height = 22
    ws.row_dimensions[sub_row].height = 18

    # --- Data rows ---
    data_start = sub_row + 1
    MEDAL = {1: GOLD, 2: SILVER, 3: BRONZE}

    for idx, lb_entry in enumerate(leaderboard_entries):
        r = data_start + idx
        entry = lb_entry.entry
        judges_who_scored = Score.objects.filter(entry=entry).values('judge').distinct().count()
        row_bg = MEDAL.get(lb_entry.rank, ALT_ROW if idx % 2 == 0 else WHITE)

        values = [
            (lb_entry.rank,                                                    "center", None),
            (entry.title,                                                      "left",   None),
            (entry.category.name if entry.category else "—",                  "left",   None),
            (entry.participant_name,                                           "left",   None),
            (entry.participant_email,                                          "left",   None),
            (entry.submitted_at.strftime('%Y-%m-%d %H:%M'),                   "center", None),
            (judges_who_scored,                                                "center", None),
            (round(lb_entry.total_weighted_score, 2),                         "center", "0.00"),
        ]
        for col, (val, align, nfmt) in enumerate(values, start=1):
            c = cell_style(ws, r, col, val, bg=row_bg, align=align, num_fmt=nfmt)
            if lb_entry.rank in MEDAL:
                c.font = Font(bold=True, name="Calibri", size=10,
                              color="000000" if lb_entry.rank == 1 else "000000")

        col = 9
        for crit in criteria_list:
            scores = Score.objects.filter(entry=entry, criteria=crit)
            if scores.exists():
                avg = scores.aggregate(Avg('score_value'))['score_value__avg']
                cell_style(ws, r, col,     round(avg, 2) if avg else 0,
                           bg=row_bg, align="center", num_fmt="0.00")
                cell_style(ws, r, col + 1, scores.count(),
                           bg=row_bg, align="center")
            else:
                cell_style(ws, r, col,     "—", bg=row_bg, align="center")
                cell_style(ws, r, col + 1, 0,   bg=row_bg, align="center")
            col += 2

        ws.row_dimensions[r].height = 16

    data_end = data_start + len(leaderboard_entries) - 1

    # --- Column widths ---
    col_widths = [6, 32, 18, 22, 30, 17, 13, 13]
    for i, w in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    col = 9
    for c in criteria_list:
        ws.column_dimensions[get_column_letter(col)].width = 14
        ws.column_dimensions[get_column_letter(col + 1)].width = 10
        col += 2

    # ── Sheet 2: Score Chart ──────────────────────────────────────────────────
    wc = wb.create_sheet("Score Chart")

    # Write a small data table the chart will reference (top 15 entries max)
    chart_entries = leaderboard_entries[:15]
    wc.cell(row=1, column=1, value="Entry").font = Font(bold=True)
    wc.cell(row=1, column=2, value="Total Score").font = Font(bold=True)
    for i, lb in enumerate(chart_entries, start=2):
        wc.cell(row=i, column=1, value=lb.entry.title)
        wc.cell(row=i, column=2, value=round(lb.total_weighted_score, 2))

    chart = BarChart()
    chart.type = "bar"          # horizontal bars
    chart.grouping = "clustered"
    chart.title = f"{competition.title} – Top Scores"
    chart.y_axis.title = "Entry"
    chart.x_axis.title = "Total Weighted Score"
    chart.style = 10
    chart.width = 22
    chart.height = max(10, len(chart_entries) * 0.9)

    data_ref = Reference(wc, min_col=2, min_row=1,
                         max_row=1 + len(chart_entries))
    cats_ref = Reference(wc, min_col=1, min_row=2,
                         max_row=1 + len(chart_entries))
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.series[0].graphicalProperties.solidFill = "2E75B6"

    wc.add_chart(chart, "D2")
    wc.column_dimensions["A"].width = 32
    wc.column_dimensions["B"].width = 14

    # ── Stream response ──────────────────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    response = HttpResponse(
        buf.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
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
