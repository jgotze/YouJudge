from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Email verification
    path('verify/<uuid:token>/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),

    # Password reset
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/<uuid:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),

    # Subscription
    path('paywall/', views.paywall_view, name='paywall'),
    path('simulate-payment/', views.simulate_payment_view, name='simulate_payment'),
]
