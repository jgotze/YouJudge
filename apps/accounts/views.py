from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from .forms import (
    UserRegistrationForm, UserLoginForm, PasswordResetRequestForm,
    PasswordResetConfirmForm, ProfileUpdateForm, PasswordUpdateForm
)
from .models import EmailVerificationToken, PasswordResetToken
from .tasks import send_verification_email, send_password_reset_email

User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect('competitions:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.email_verified = False
            user.save()

            token = EmailVerificationToken.objects.create(user=user)
            send_verification_email.delay(user.id, str(token.token))

            messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('competitions:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_short_name()}!')

            next_url = request.GET.get('next', 'competitions:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('landing')


def verify_email_view(request, token):
    verification_token = get_object_or_404(EmailVerificationToken, token=token)

    if verification_token.is_valid():
        user = verification_token.user
        user.email_verified = True
        user.save()

        EmailVerificationToken.objects.filter(user=user).delete()

        messages.success(request, 'Email verified successfully! You can now login.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('landing')


def resend_verification_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                messages.info(request, 'Your email is already verified.')
            else:
                EmailVerificationToken.objects.filter(user=user).delete()
                token = EmailVerificationToken.objects.create(user=user)
                send_verification_email.delay(user.id, str(token.token))
                messages.success(request, 'Verification email sent! Please check your inbox.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
        except Exception:
            messages.error(request, 'Failed to send verification email. Please try again later.')

    return render(request, 'accounts/resend_verification.html')


def password_reset_request_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)

                PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
                token = PasswordResetToken.objects.create(user=user)
                send_password_reset_email.delay(user.id, str(token.token))

            except User.DoesNotExist:
                pass
            except Exception:
                messages.error(request, 'Failed to send reset email. Please try again later.')
                return render(request, 'accounts/password_reset_request.html', {'form': form})

            messages.success(request, 'If an account exists with this email, a reset link will be sent.')
            return redirect('accounts:login')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token)

    if not reset_token.is_valid():
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('accounts:password_reset_request')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data['password1'])
            user.save()

            reset_token.used = True
            reset_token.save()

            messages.success(request, 'Password reset successfully! You can now login.')
            return redirect('accounts:login')
    else:
        form = PasswordResetConfirmForm()

    return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'token': token})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordUpdateForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
    else:
        form = PasswordUpdateForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def paywall_view(request):
    if request.user.is_subscribed:
        return redirect('competitions:dashboard')
    return render(request, 'accounts/paywall.html')


@login_required
def simulate_payment_view(request):
    if request.method == 'POST':
        request.user.is_subscribed = True
        request.user.save(update_fields=['is_subscribed'])
        messages.success(request, "You're now a client! Welcome to YouJudge.")
        return redirect('accounts:profile')
    return redirect('accounts:paywall')
