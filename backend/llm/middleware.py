import uuid

class AnonymousSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if 'anon_id' not in request.COOKIES:
            session_id = str(uuid.uuid4())
            print("Creating new session ID: ", session_id)
            response.set_cookie(
                'anon_session_id',
                session_id,
                max_age=60 * 60 * 24 * 365,
                samesite='Lax',  # wichtig, damit CORS nicht blockiert
                httponly=False,  # muss False sein, wenn Nuxt darauf zugreift
                secure=False,  # bei http: False (lokal), bei https: True
                path='/'
            )

        return response