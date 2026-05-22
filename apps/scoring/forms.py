from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, HTML, Div
from .models import Score


class ScoreForm(forms.ModelForm):
    """Form for scoring entries."""

    class Meta:
        model = Score
        fields = ['score_value', 'comment']
        widgets = {
            'score_value': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional comment...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = False

        # Add custom CSS classes for radio buttons
        self.fields['score_value'].widget.attrs.update({'class': 'btn-check'})


class BulkScoreForm(forms.Form):
    """Form for scoring multiple criteria for a single entry."""

    def __init__(self, *args, **kwargs):
        entry = kwargs.pop('entry', None)
        judge = kwargs.pop('judge', None)
        super().__init__(*args, **kwargs)

        if entry:
            max_score = entry.competition.max_score
            # Create a field for each criteria
            for criteria in entry.competition.criteria.all():
                # Try to get existing score
                existing_score = None
                if judge:
                    try:
                        existing_score = Score.objects.get(
                            judge=judge,
                            entry=entry,
                            criteria=criteria
                        )
                    except Score.DoesNotExist:
                        pass

                # Score value field
                field_name = f'score_{criteria.id}'
                self.fields[field_name] = forms.IntegerField(
                    label=f'{criteria.title} (Weight: {criteria.weight})',
                    help_text=criteria.description if criteria.description else '',
                    min_value=0,
                    max_value=max_score,
                    required=True,
                    initial=existing_score.score_value if existing_score else None,
                    widget=forms.Select(choices=[(i, str(i)) for i in range(0, max_score + 1)])
                )

                # Comment field
                comment_field_name = f'comment_{criteria.id}'
                self.fields[comment_field_name] = forms.CharField(
                    label='Comment (Optional)',
                    required=False,
                    initial=existing_score.comment if existing_score else '',
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Share your thoughts on this criteria…'})
                )

        self.helper = FormHelper()
        self.helper.form_method = 'post'
