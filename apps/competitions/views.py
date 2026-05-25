from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.urls import reverse
from .models import Competition, JudgeAssignment, Criteria, Entry, PendingJudgeInvite, Category
from .forms import (
    CompetitionForm, JudgeAssignmentForm, GlobalJudgeInviteForm, CriteriaForm,
    EntryForm, CompetitionStatusForm, CategoryForm
)
from apps.notifications.models import Notification
from apps.accounts.tasks import send_judge_invite_email, send_external_judge_invite_email

User = get_user_model()

@login_required
def my_judges_view(request):
    if request.method == 'POST':
        form = GlobalJudgeInviteForm(request.user, request.POST)
        if form.is_valid():
            competition = form.cleaned_data['competition']
            emails = form.cleaned_data['judge_emails']
            inviter_name = request.user.get_full_name() or request.user.email
            dashboard_url = request.build_absolute_uri(reverse('competitions:dashboard'))
            register_url = request.build_absolute_uri(reverse('accounts:register'))

            for email in emails:
                try:
                    judge = User.objects.get(email=email)
                    JudgeAssignment.objects.create(
                        competition=competition,
                        judge=judge,
                        status='invited'
                    )
                    Notification.objects.create(
                        user=judge,
                        title='Judge Invitation',
                        message=f'{inviter_name} invited you to judge "{competition.title}".',
                        notification_type='judge_invited',
                        related_object_id=str(competition.id),
                        related_object_type='competition'
                    )
                    if judge != request.user:
                        send_judge_invite_email.delay(
                            str(judge.id), competition.title, inviter_name, dashboard_url
                        )
                except User.DoesNotExist:
                    PendingJudgeInvite.objects.get_or_create(
                        email=email,
                        competition=competition,
                        defaults={'invited_by': request.user}
                    )
                    send_external_judge_invite_email.delay(
                        email, competition.title, inviter_name, register_url
                    )

            if len(emails) == 1:
                messages.success(request, f'Invitation sent to {emails[0]}.')
            else:
                messages.success(request, f'{len(emails)} invitations sent successfully.')
            return redirect('competitions:my_judges')
    else:
        form = GlobalJudgeInviteForm(request.user)

    assignments = JudgeAssignment.objects.filter(
        competition__created_by=request.user
    ).select_related('judge', 'competition').order_by('competition__title', 'judge__email')

    my_competitions = Competition.objects.filter(created_by=request.user)

    return render(request, 'competitions/my_judges.html', {
        'assignments': assignments,
        'my_competitions': my_competitions,
        'invite_form': form,
    })


@login_required
def dashboard_view(request):
    """Display user dashboard with competitions."""
    my_competitions = Competition.objects.filter(created_by=request.user).order_by('-created_at')

    context = {
        'my_competitions': my_competitions,
    }
    return render(request, 'competitions/dashboard.html', context)


@login_required
def competition_create_view(request):
    """Create a new competition."""
    if not request.user.is_subscribed:
        return redirect('accounts:paywall')

    if request.method == 'POST':
        form = CompetitionForm(request.POST, request.FILES)
        if form.is_valid():
            competition = form.save(commit=False)
            competition.created_by = request.user
            competition.save()
            messages.success(request, 'Competition created successfully!')
            return redirect('competitions:detail', pk=competition.pk)
    else:
        form = CompetitionForm()

    return render(request, 'competitions/competition_form.html', {'form': form, 'action': 'Create'})


@login_required
def competition_detail_view(request, pk):
    """Display competition details."""
    competition = get_object_or_404(Competition, pk=pk)
    competition.sync_status()

    # Check permissions
    is_owner = competition.created_by == request.user
    is_judge = competition.can_user_judge(request.user)

    if not (is_owner or is_judge):
        raise PermissionDenied("You don't have permission to view this competition.")

    judges = JudgeAssignment.objects.filter(competition=competition).select_related('judge')
    pending_invites = PendingJudgeInvite.objects.filter(competition=competition)
    criteria = competition.criteria.all()
    entries = competition.entries.select_related('category').all()
    categories = competition.categories.all()
    owner_is_judge = judges.filter(judge=request.user, status='accepted').exists()

    context = {
        'competition': competition,
        'is_owner': is_owner,
        'is_judge': is_judge,
        'owner_is_judge': owner_is_judge,
        'judges': judges,
        'pending_invites': pending_invites,
        'criteria': criteria,
        'entries': entries,
        'categories': categories,
        'entry_form': EntryForm(competition=competition),
        'category_form': CategoryForm(),
        'judge_form': JudgeAssignmentForm(competition=competition),
        'criteria_form': CriteriaForm(),
    }
    return render(request, 'competitions/competition_detail.html', context)


@login_required
def competition_edit_view(request, pk):
    """Edit competition."""
    competition = get_object_or_404(Competition, pk=pk)

    if not competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to edit this competition.")

    if request.method == 'POST':
        form = CompetitionForm(request.POST, request.FILES, instance=competition)
        if form.is_valid():
            form.save()
            messages.success(request, 'Competition updated successfully!')
            return redirect('competitions:detail', pk=competition.pk)
    else:
        form = CompetitionForm(instance=competition)

    return render(request, 'competitions/competition_form.html', {
        'form': form,
        'competition': competition,
        'action': 'Edit'
    })


@login_required
def competition_delete_view(request, pk):
    """Delete competition."""
    competition = get_object_or_404(Competition, pk=pk)

    if not competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to delete this competition.")

    if request.method == 'POST':
        competition.delete()
        messages.success(request, 'Competition deleted successfully!')
        return redirect('competitions:dashboard')

    return render(request, 'competitions/competition_confirm_delete.html', {'competition': competition})


@login_required
def competition_status_update_view(request, pk):
    """Update competition status."""
    competition = get_object_or_404(Competition, pk=pk)

    if not competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to update this competition.")

    if request.method == 'POST':
        form = CompetitionStatusForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            competition.status = new_status
            competition.save()

            # Send notifications to judges
            if new_status == 'active':
                judges = JudgeAssignment.objects.filter(
                    competition=competition,
                    status='accepted'
                )
                for assignment in judges:
                    Notification.objects.create(
                        user=assignment.judge,
                        title='Competition Started',
                        message=f'"{competition.title}" has started. You can now begin scoring entries.',
                        notification_type='competition_started',
                        related_object_id=str(competition.id),
                        related_object_type='competition'
                    )

            messages.success(request, f'Competition status updated to {new_status}!')
            return redirect('competitions:detail', pk=competition.pk)
    else:
        form = CompetitionStatusForm(initial={'status': competition.status})

    return render(request, 'competitions/competition_status_form.html', {
        'form': form,
        'competition': competition
    })


@login_required
def judge_add_self_view(request, pk):
    """Toggle the competition owner as a judge on their own competition."""
    competition = get_object_or_404(Competition, pk=pk)

    if not competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to modify judges.")

    if request.method == 'POST':
        existing = JudgeAssignment.objects.filter(
            competition=competition,
            judge=request.user
        ).first()

        if existing:
            existing.delete()
            messages.success(request, 'You have been removed as a judge.')
        else:
            JudgeAssignment.objects.create(
                competition=competition,
                judge=request.user,
                status='accepted'
            )
            messages.success(request, 'You have been added as a judge.')

    return redirect(reverse('competitions:detail', kwargs={'pk': competition.pk}) + '#judges')


@login_required
def judge_invite_view(request, pk):
    """Invite a judge to a competition."""
    competition = get_object_or_404(Competition, pk=pk)

    if not competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to invite judges.")

    if request.method == 'POST':
        form = JudgeAssignmentForm(request.POST, competition=competition)
        if form.is_valid():
            emails = form.cleaned_data['judge_emails']
            inviter_name = request.user.get_full_name() or request.user.email
            dashboard_url = request.build_absolute_uri(reverse('competitions:dashboard'))
            register_url = request.build_absolute_uri(reverse('accounts:register'))

            for email in emails:
                try:
                    judge = User.objects.get(email=email)
                    # User exists — create assignment
                    JudgeAssignment.objects.create(
                        competition=competition,
                        judge=judge,
                        status='invited'
                    )
                    Notification.objects.create(
                        user=judge,
                        title='Judge Invitation',
                        message=f'{inviter_name} invited you to judge "{competition.title}".',
                        notification_type='judge_invited',
                        related_object_id=str(competition.id),
                        related_object_type='competition'
                    )
                    # Skip email if inviting yourself
                    if judge != request.user:
                        send_judge_invite_email.delay(
                            str(judge.id), competition.title, inviter_name, dashboard_url
                        )
                except User.DoesNotExist:
                    # No account — store a pending invite so it activates on signup
                    PendingJudgeInvite.objects.get_or_create(
                        email=email,
                        competition=competition,
                        defaults={'invited_by': request.user}
                    )
                    send_external_judge_invite_email.delay(
                        email, competition.title, inviter_name, register_url
                    )

            if len(emails) == 1:
                messages.success(request, f'Invitation sent to {emails[0]}.')
            else:
                messages.success(request, f'{len(emails)} invitations sent successfully.')

            return redirect(reverse('competitions:detail', kwargs={'pk': competition.pk}) + '#judges')
    else:
        form = JudgeAssignmentForm(competition=competition)

    return render(request, 'competitions/judge_invite_form.html', {
        'form': form,
        'competition': competition
    })


@login_required
def judge_assignment_respond_view(request, pk, action):
    """Accept or decline judge assignment."""
    assignment = get_object_or_404(JudgeAssignment, pk=pk)

    if assignment.judge != request.user:
        raise PermissionDenied("You don't have permission to respond to this invitation.")

    if action == 'accept':
        assignment.accept()
        messages.success(request, f'You have accepted the invitation to judge "{assignment.competition.title}"!')

        # Notify competition creator
        Notification.objects.create(
            user=assignment.competition.created_by,
            title='Judge Accepted',
            message=f'{request.user.get_short_name()} accepted to judge "{assignment.competition.title}"',
            notification_type='judge_accepted',
            related_object_id=str(assignment.competition.id),
            related_object_type='competition'
        )
    elif action == 'decline':
        assignment.decline()
        messages.info(request, f'You have declined the invitation to judge "{assignment.competition.title}".')

    return redirect('competitions:dashboard')


@login_required
def judge_remove_view(request, pk):
    """Remove a judge from a competition."""
    assignment = get_object_or_404(JudgeAssignment, pk=pk)

    if not assignment.competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to remove judges.")

    if request.method == 'POST':
        competition_pk = assignment.competition.pk
        assignment.delete()
        messages.success(request, 'Judge removed successfully!')
        return redirect('competitions:detail', pk=competition_pk)

    return render(request, 'competitions/judge_confirm_delete.html', {'assignment': assignment})


@login_required
def criteria_create_view(request, competition_pk):
    """Create a new criteria for a competition."""
    competition = get_object_or_404(Competition, pk=competition_pk)

    if not competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to add criteria.")

    if request.method == 'POST':
        form = CriteriaForm(request.POST)
        if form.is_valid():
            criteria = form.save(commit=False)
            criteria.competition = competition
            criteria.save()
            messages.success(request, 'Criteria added successfully!')
            return redirect(reverse('competitions:detail', kwargs={'pk': competition.pk}) + '#criteria')
    else:
        form = CriteriaForm()

    return render(request, 'competitions/criteria_form.html', {
        'form': form,
        'competition': competition,
        'action': 'Add'
    })


@login_required
def criteria_edit_view(request, pk):
    """Edit criteria."""
    criteria = get_object_or_404(Criteria, pk=pk)

    if not criteria.competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to edit criteria.")

    if request.method == 'POST':
        form = CriteriaForm(request.POST, instance=criteria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Criteria updated successfully!')
            return redirect(reverse('competitions:detail', kwargs={'pk': criteria.competition.pk}) + '#criteria')
    else:
        form = CriteriaForm(instance=criteria)

    return render(request, 'competitions/criteria_form.html', {
        'form': form,
        'competition': criteria.competition,
        'criteria': criteria,
        'action': 'Edit'
    })


@login_required
def criteria_delete_view(request, pk):
    """Delete criteria."""
    criteria = get_object_or_404(Criteria, pk=pk)

    if not criteria.competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to delete criteria.")

    if request.method == 'POST':
        competition_pk = criteria.competition.pk
        criteria.delete()
        messages.success(request, 'Criteria deleted successfully!')
        return redirect('competitions:detail', pk=competition_pk)

    return render(request, 'competitions/criteria_confirm_delete.html', {'criteria': criteria})


@login_required
def entry_create_view(request, competition_pk):
    """Create a new entry for a competition."""
    competition = get_object_or_404(Competition, pk=competition_pk)

    if request.method == 'POST':
        form = EntryForm(request.POST, request.FILES, competition=competition)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.competition = competition
            entry.submitted_by = request.user
            entry.save()
            messages.success(request, 'Entry submitted successfully!')
            return redirect(reverse('competitions:detail', kwargs={'pk': competition.pk}) + '#entries')
    else:
        form = EntryForm(competition=competition)

    return render(request, 'competitions/entry_form.html', {
        'form': form,
        'competition': competition,
        'action': 'Submit'
    })


@login_required
def entry_edit_view(request, pk):
    """Edit entry."""
    entry = get_object_or_404(Entry, pk=pk)

    # Only owner or submitter can edit
    if not (entry.competition.can_user_edit(request.user) or entry.submitted_by == request.user):
        raise PermissionDenied("You don't have permission to edit this entry.")

    if request.method == 'POST':
        form = EntryForm(request.POST, request.FILES, instance=entry, competition=entry.competition)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entry updated successfully!')
            return redirect(reverse('competitions:detail', kwargs={'pk': entry.competition.pk}) + '#entries')
    else:
        form = EntryForm(instance=entry, competition=entry.competition)

    return render(request, 'competitions/entry_form.html', {
        'form': form,
        'competition': entry.competition,
        'entry': entry,
        'action': 'Edit'
    })


@login_required
def category_create_view(request, competition_pk):
    """Create a category for a competition."""
    competition = get_object_or_404(Competition, pk=competition_pk)

    if not competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to add categories.")

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Category.objects.filter(competition=competition, name=name).exists():
                messages.error(request, f'A category named "{name}" already exists.')
            else:
                category = form.save(commit=False)
                category.competition = competition
                category.save()
                messages.success(request, f'Category "{category.name}" added.')
        else:
            messages.error(request, 'Invalid category name.')

    return redirect(reverse('competitions:detail', kwargs={'pk': competition.pk}) + '#entries')


@login_required
def category_delete_view(request, pk):
    """Delete a category."""
    category = get_object_or_404(Category, pk=pk)

    if not category.competition.can_user_edit(request.user):
        raise PermissionDenied("You don't have permission to delete this category.")

    if request.method == 'POST':
        competition_pk = category.competition.pk
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect(reverse('competitions:detail', kwargs={'pk': competition_pk}) + '#entries')

    return redirect(reverse('competitions:detail', kwargs={'pk': category.competition.pk}) + '#entries')


@login_required
def entry_delete_view(request, pk):
    """Delete entry."""
    entry = get_object_or_404(Entry, pk=pk)

    # Only owner or submitter can delete
    if not (entry.competition.can_user_edit(request.user) or entry.submitted_by == request.user):
        raise PermissionDenied("You don't have permission to delete this entry.")

    if request.method == 'POST':
        competition_pk = entry.competition.pk
        entry.delete()
        messages.success(request, 'Entry deleted successfully!')
        return redirect('competitions:detail', pk=competition_pk)

    return render(request, 'competitions/entry_confirm_delete.html', {'entry': entry})
