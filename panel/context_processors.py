from website.models import QuoteRequest


def panel(request):
    """Badge count for the sidebar; only computed on panel pages for staff."""
    match = getattr(request, "resolver_match", None)
    if not match or match.app_name != "panel":
        return {}
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated and user.is_staff):
        return {}
    return {"new_inquiry_count": QuoteRequest.objects.filter(status=QuoteRequest.Status.NEW).count()}
