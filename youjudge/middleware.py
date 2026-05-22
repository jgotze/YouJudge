from django.shortcuts import redirect
from django.urls import reverse


EXEMPT_PREFIXES = (
    '/accounts/',
    '/admin/',
    '/api/',
    '/paywall/',
    '/static/',
    '/media/',
)

# Paths only subscribed users can access (free judges are blocked here)
SUBSCRIPTION_ONLY_PATHS = (
    '/dashboard/competitions/create/',
)


class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            path = request.path

            # Skip checks for exempt paths and the landing page
            if path == '/' or any(path.startswith(p) for p in EXEMPT_PREFIXES):
                return self.get_response(request)

            if not request.user.is_subscribed:
                # Lazy import to avoid circular imports at module load
                from apps.competitions.models import JudgeAssignment

                has_judge_access = JudgeAssignment.objects.filter(
                    judge=request.user,
                    status__in=['invited', 'accepted'],
                    deleted_at__isnull=True,
                ).exists()

                if not has_judge_access:
                    # No subscription, no judge role → full paywall
                    return redirect(reverse('accounts:paywall'))

                # Has judge access but no subscription → block creation only
                if any(path.startswith(p) for p in SUBSCRIPTION_ONLY_PATHS):
                    return redirect(reverse('accounts:paywall'))

        return self.get_response(request)
