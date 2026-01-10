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
    return HttpResponse("""
    <h1>BizBooks API</h1>
    <p>Welcome to the BizBooks accounting backend.</p>
    <ul>
        <li><a href="/admin/">Admin</a></li>
        <li><a href="/api/">API Root</a></li>
    </ul>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounting.urls')),
    path('', home_view),
]