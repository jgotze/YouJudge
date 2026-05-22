from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', css_class='mb-3'),
            Row(
                Column('first_name', css_class='mb-3'),
                Column('last_name', css_class='mb-3'),
            ),
            Field('password1', css_class='mb-3'),
            Field('password2', css_class='mb-3'),
            Submit('submit', 'Sign Up', css_class='btn btn-primary w-100')
        )

        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
        self.fields['password1'].help_text = 'At least 8 characters — cannot be entirely numeric.'
        self.fields['password2'].help_text = 'Enter the same password again to confirm.'


class UserLoginForm(AuthenticationForm):
    """Form for user login."""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='mb-3'),
            Field('password', css_class='mb-3'),
            Submit('submit', 'Login', css_class='btn btn-primary w-100')
        )


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset."""

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', css_class='mb-3'),
            Submit('submit', 'Send Reset Link', css_class='btn btn-primary w-100')
        )


class PasswordResetConfirmForm(forms.Form):
    """Form for resetting password."""

    password1 = forms.CharField(
        label='New Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('password1', css_class='mb-3'),
            Field('password2', css_class='mb-3'),
            Submit('submit', 'Reset Password', css_class='btn btn-primary w-100')
        )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match.")
            try:
                validate_password(password1)
            except forms.ValidationError as e:
                self.add_error('password1', e)

        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'phone', 'organization', 'avatar', 'email_notifications']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your last name'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us a bit about yourself…'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +27 82 123 4567'}),
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. University of Cape Town'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].help_text = 'Upload a profile photo (JPG or PNG). Optional.'
        self.fields['email_notifications'].help_text = 'Receive email updates about competitions and judging activity.'
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='mb-3'),
                Column('last_name', css_class='mb-3'),
            ),
            Field('email_notifications', css_class='mb-3'),
            Field('bio', css_class='mb-3'),
            Row(
                Column('phone', css_class='mb-3'),
                Column('organization', css_class='mb-3'),
            ),
            Field('avatar', css_class='mb-3'),
            Submit('submit', 'Update Profile', css_class='btn btn-primary')
        )


class PasswordUpdateForm(PasswordChangeForm):
    """Form for changing password."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('old_password', css_class='mb-3'),
            Field('new_password1', css_class='mb-3'),
            Field('new_password2', css_class='mb-3'),
            Submit('submit', 'Change Password', css_class='btn btn-primary')
        )

        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Your current password'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Choose a new password'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Repeat your new password'})
        self.fields['new_password1'].help_text = 'At least 8 characters — cannot be entirely numeric.'
        self.fields['new_password2'].help_text = 'Enter the same password again to confirm.'
