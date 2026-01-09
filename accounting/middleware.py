from django.utils.functional import SimpleLazyObject
from .models import User


def get_accounting_user(request):
    user_id = request.session.get('accounting_user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None


class AccountingSessionAuthMiddleware:
    """Middleware that populates `request.user` from `request.session['accounting_user_id']`.

    Place after Django's `AuthenticationMiddleware` so it can override request.user when an
    accounting session is present. This is a lightweight development helper and not a full
    replacement for a production auth backend.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = get_accounting_user(request)
        if user is not None:
            # wrap user in SimpleLazyObject to mimic Django user behavior
            request.user = SimpleLazyObject(lambda: user)
            # mark as authenticated for DRF `IsAuthenticated` checks
            try:
                request.user.is_authenticated = True
            except Exception:
                pass
        return self.get_response(request)
