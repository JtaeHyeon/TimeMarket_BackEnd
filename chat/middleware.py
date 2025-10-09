from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser
from users.models import User

@database_sync_to_async
def get_user_from_token(token):
    try:
        user_id = AccessToken(token)["user_id"]
        return User.objects.get(id=user_id)
    except:
        return AnonymousUser()

def JWTAuthMiddleware(inner):
    async def middleware(scope, receive, send):
        print(f"🔍 미들웨어 처리 - scope type: {scope['type']}, path: {scope.get('path', 'N/A')}")
        
        query_string = scope["query_string"].decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]
        
        print(f"🔑 토큰: {token[:50] if token else 'None'}...")

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()
            
        print(f"👤 사용자: {scope['user']}")

        return await inner(scope, receive, send)

    return middleware
