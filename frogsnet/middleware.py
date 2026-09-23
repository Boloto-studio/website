from django.utils import timezone


class UpdateLastActivityMiddleware:
    """Middleware that sets `request.user.frog.last_activity` to now on each request

    Safe no-op when the user is anonymous or doesn't have a related `frog`.
    Updates the field using `save(update_fields=['last_activity'])` to avoid
    touching other fields or triggering unrelated signals.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            # user may not have a frog if migrations/creation haven't run; guard it
            frog = getattr(user, 'frog', None)
            if frog is not None:
                try:
                    frog.last_activity = timezone.now()
                    frog.save(update_fields=['last_activity'])
                except Exception:
                    # Don't let any failure here break the request; keep silent
                    pass

        response = self.get_response(request)
        return response
