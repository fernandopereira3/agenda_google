from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class ContentSecurityPolicyMiddleware:
    """Adiciona o header Content-Security-Policy em todas as respostas."""

    def __init__(self, get_response):
        self.get_response = get_response
        directives = getattr(settings, "CSP_DIRECTIVES", {})
        self._policy = "; ".join(
            f"{key} {' '.join(values) if isinstance(values, (list, tuple)) else values}"
            for key, values in directives.items()
        )

    def __call__(self, request):
        response = self.get_response(request)
        if self._policy:
            response["Content-Security-Policy"] = self._policy
        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        return response


class MobileDetectionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        if "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent:
            request.is_mobile = True
        else:
            request.is_mobile = False
