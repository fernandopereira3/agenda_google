def google_calendar_status(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"google_conectado": False}
    return {
        "google_conectado": user.socialaccount_set.filter(provider="google").exists()
    }
