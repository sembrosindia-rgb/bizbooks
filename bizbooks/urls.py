"""
URL configuration for bizbooks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('api/', include('accounting.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home_view(request):
    from django.middleware.csrf import get_token
    csrf_token = get_token(request)
    message = ""
    if request.method == 'POST':
        if 'signup' in request.POST:
            # Handle sign-up
            from accounting.serializers import UserCreateSerializer
            serializer = UserCreateSerializer(data=request.POST)
            if serializer.is_valid():
                user = serializer.save()
                from accounting.models import AuditLog
                AuditLog.objects.create(user=user, action='signup')
                from accounting.models import GlobalSettings
                settings = GlobalSettings.objects.first()
                if settings and (settings.email_verification_required or settings.phone_verification_required):
                    message = 'Account created! Please verify your email/phone.'
                else:
                    from rest_framework.authtoken.models import Token
                    token, _ = Token.objects.get_or_create(user=user)
                    message = f'Account created! Your token: {token.key}'
            else:
                message = f'Sign-up errors: {str(serializer.errors)}'
        elif 'login' in request.POST:
            # Handle login
            from accounting.serializers import LoginSerializer
            serializer = LoginSerializer(data=request.POST)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                from django.contrib.auth import login
                login(request, user)
                from rest_framework.authtoken.models import Token
                token, _ = Token.objects.get_or_create(user=user)
                message = f'Logged in! Your token: {token.key}'
            else:
                message = f'Login errors: {str(serializer.errors)}'
    
    signup_form = f"""
    <h2>Sign Up</h2>
    <form method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
        <input type="hidden" name="signup" value="1">
        <label>Username: <input type="text" name="username" required></label><br>
        <label>Email: <input type="email" name="email" required></label><br>
        <label>Password: <input type="password" name="password" required></label><br>
        <label>Confirm Password: <input type="password" name="password_confirm" required></label><br>
        <label>First Name: <input type="text" name="first_name"></label><br>
        <label>Last Name: <input type="text" name="last_name"></label><br>
        <label>Phone Number: <input type="text" name="phone_number"></label><br>
        <button type="submit">Sign Up</button>
    </form>
    """
    
    login_form = f"""
    <h2>Login</h2>
    <form method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
        <input type="hidden" name="login" value="1">
        <label>Username: <input type="text" name="username" required></label><br>
        <label>Password: <input type="password" name="password" required></label><br>
        <button type="submit">Login</button>
    </form>
    """
    
    return HttpResponse(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BizBooks</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #007bff; text-align: center; }}
            h2 {{ color: #28a745; }}
            form {{ margin-bottom: 20px; }}
            label {{ display: block; margin: 10px 0 5px; }}
            input {{ width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
            button {{ padding: 10px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; width: 100%; }}
            button:hover {{ background-color: #218838; }}
            .message {{ color: red; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏢 BizBooks</h1>
            <p>Welcome! Sign up or login to get started.</p>
            {signup_form}
            {login_form}
            <p class="message">{message}</p>
        </div>
    </body>
    </html>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounting.urls')),
    path('', home_view),
]