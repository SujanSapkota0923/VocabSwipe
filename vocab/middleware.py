from django.http import JsonResponse
from django.conf import settings


class ApiAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Enforce API password only for list deletion
        if request.method == "POST" and request.path.startswith("/api/delete-list/"):
            password = request.headers.get("X-Api-Password") or request.GET.get(
                "password"
            )
            if not password or password != settings.API_PASSWORD:
                return JsonResponse({"error": "Unauthorized"}, status=401)

        # Game endpoints (/api/cards/, /api/word-lists/) are now public as requested
        response = self.get_response(request)
        return response
