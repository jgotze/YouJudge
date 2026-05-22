from django import forms
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from .models import Competition, JudgeAssignment, Criteria, Entry, Category

User = get_user_model()


class CompetitionForm(forms.ModelForm):
    """Form for creating and editing competitions."""

    class Meta:
        model = Competition
        fields = ['title', 'description', 'icon', 'color', 'start_date', 'end_date', 'max_score']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Regional Science Fair 2025'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the competition, its rules, and objectives…'}),
            'icon': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.HiddenInput(),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 1000, 'placeholder': 'e.g. 10'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['start_date'].help_text = 'Date and time when entries open.'
        self.fields['end_date'].help_text = 'Date and time when entries close.'
        self.fields['max_score'].help_text = 'Maximum score a judge can give per criteria (e.g. 10).'
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', css_class='mb-3'),
            Field('description', css_class='mb-3'),
            Field('icon', css_class='mb-3'),
            Field('color'),
            Row(
                Column('start_date', css_class='mb-3'),
                Column('end_date', css_class='mb-3'),
            ),
            Field('max_score', css_class='mb-3'),
            Submit('submit', 'Save Competition', css_class='btn btn-primary')
        )


class JudgeAssignmentForm(forms.Form):
    """Form for assigning judges to a competition."""

    judge_emails = forms.CharField(
        label='Judge Email(s)',
        help_text="Separate multiple addresses with semicolons. Non-registered users will receive an invitation to sign up.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'alice@example.com; bob@example.com'
        })
    )

    def __init__(self, *args, **kwargs):
        self.competition = kwargs.pop('competition', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('judge_emails', css_class='mb-3'),
            Submit('submit', 'Invite Judges', css_class='btn btn-primary')
        )

    def clean_judge_emails(self):
        raw = self.cleaned_data['judge_emails']
        emails = [e.strip() for e in raw.split(';') if e.strip()]
        if not emails:
            raise forms.ValidationError('Please enter at least one email address.')

        email_validator = forms.EmailField()
        errors = []
        valid_emails = []
        for email in emails:
            try:
                email_validator.clean(email)
            except forms.ValidationError:
                errors.append(f'"{email}" is not a valid email address.')
                continue

            try:
                user = User.objects.get(email=email)
                if self.competition and JudgeAssignment.objects.filter(
                    competition=self.competition,
                    judge=user
                ).exists():
                    errors.append(f'{email} is already a judge for this competition.')
                    continue
            except User.DoesNotExist:
                pass  # No account yet — will send a join invite instead

            valid_emails.append(email)

        if errors:
            raise forms.ValidationError(errors)

        return valid_emails


class GlobalJudgeInviteForm(forms.Form):
    """Invite judges from the My Judges page — includes a competition selector."""

    competition = forms.ModelChoiceField(
        queryset=Competition.objects.none(),
        label='Competition',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    judge_emails = forms.CharField(
        label='Judge Email(s)',
        help_text="Separate multiple addresses with semicolons. Non-registered users will receive an invitation to sign up.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'alice@example.com; bob@example.com'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['competition'].queryset = Competition.objects.filter(created_by=user)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('competition', css_class='mb-3'),
            Field('judge_emails', css_class='mb-3'),
            Submit('submit', 'Invite Judges', css_class='btn btn-primary w-100')
        )

    def clean_judge_emails(self):
        raw = self.cleaned_data['judge_emails']
        emails = [e.strip() for e in raw.split(';') if e.strip()]
        if not emails:
            raise forms.ValidationError('Please enter at least one email address.')

        competition = self.cleaned_data.get('competition')
        email_validator = forms.EmailField()
        errors = []
        valid_emails = []
        for email in emails:
            try:
                email_validator.clean(email)
            except forms.ValidationError:
                errors.append(f'"{email}" is not a valid email address.')
                continue

            if competition:
                try:
                    user = User.objects.get(email=email)
                    if JudgeAssignment.objects.filter(competition=competition, judge=user).exists():
                        errors.append(f'{email} is already a judge for this competition.')
                        continue
                except User.DoesNotExist:
                    pass

            valid_emails.append(email)

        if errors:
            raise forms.ValidationError(errors)

        return valid_emails


class CriteriaForm(forms.ModelForm):
    """Form for creating and editing criteria."""

    class Meta:
        model = Criteria
        fields = ['title', 'description', 'weight']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Presentation Quality'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe what judges should look for when evaluating this criteria…'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'placeholder': '1–5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['weight'].help_text = 'How much this criteria influences the final score (1 = least impact, 5 = most impact).'
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', css_class='mb-3'),
            Field('description', css_class='mb-3'),
            Field('weight', css_class='mb-3'),
            Submit('submit', 'Save Criteria', css_class='btn btn-primary')
        )


class CategoryForm(forms.ModelForm):
    """Form for creating a category."""

    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Red Wines'}),
        }


class EntryForm(forms.ModelForm):
    """Form for creating and editing entries."""

    class Meta:
        model = Entry
        fields = ['title', 'description', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Climate Change Research Project'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of the entry (optional)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        competition = kwargs.pop('competition', None)
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['category'].required = False
        self.fields['category'].empty_label = 'No category'
        self.fields['category'].help_text = 'Optional. Group entries by category for easier filtering.'
        if competition:
            self.fields['category'].queryset = Category.objects.filter(competition=competition)
        else:
            self.fields['category'].queryset = Category.objects.none()
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('title', css_class='mb-3'),
            Field('category', css_class='mb-3'),
            Field('description', css_class='mb-3'),
            Submit('submit', 'Save Entry', css_class='btn btn-primary')
        )


class CompetitionStatusForm(forms.Form):
    """Form for changing competition status."""

    status = forms.ChoiceField(
        choices=Competition.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].help_text = 'Draft: hidden from judges. Active: judges can score entries. Closed: scoring is locked.'
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('status', css_class='mb-3'),
            Submit('submit', 'Update Status', css_class='btn btn-warning')
        )
