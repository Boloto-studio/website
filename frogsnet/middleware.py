from datetime import timedelta

from django.utils import timezone

from .models import Frog

# Skip the DB write if activity was already recorded this recently. Far below
# the 15 minute online window in Frog.status, so it doesn't affect accuracy.
ACTIVITY_WRITE_INTERVAL = timedelta(seconds=60)


class UpdateLastActivityMiddleware:
    """Middleware that sets `request.user.frog.last_activity` to now on each request

    Safe no-op when the user is anonymous or doesn't have a related `frog`.
    Writes via a queryset `update()` so it doesn't trigger `auto_now` fields or
    save signals, and is throttled to one write per ACTIVITY_WRITE_INTERVAL.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            # user may not have a frog if migrations/creation haven't run; guard it
            frog = getattr(user, 'frog', None)
            if frog is not None:
                now = timezone.now()
                last = frog.last_activity
                if last is None or now - last >= ACTIVITY_WRITE_INTERVAL:
                    try:
                        Frog.objects.filter(pk=frog.pk).update(last_activity=now)
                        frog.last_activity = now
                    except Exception:
                        # Don't let any failure here break the request; keep silent
                        pass

        response = self.get_response(request)
        return response
