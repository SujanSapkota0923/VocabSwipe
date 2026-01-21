from django.http import JsonResponse
from django.conf import settings

class ApiAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            password = request.headers.get('X-Api-Password') or request.GET.get('password')
            
            if not password or password != settings.API_PASSWORD:
                return JsonResponse(
                    {'error': 'Unauthorized', 'message': 'Invalid or missing API password'},
                    status=401
                )

        response = self.get_response(request)
        return response
 