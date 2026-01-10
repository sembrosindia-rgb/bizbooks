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
    <h2>Quick Links</h2>
    <ul>
        <li><a href="/admin/">Admin Panel</a></li>
        <li><a href="/api/">API Root (Browsable)</a></li>
        <li><a href="/api/organizations/">Organizations</a></li>
        <li><a href="/api/parties/">Parties</a></li>
        <li><a href="/api/tax-config/">Tax Configurations</a></li>
        <li><a href="/api/plans/">Plans</a></li>
        <li><a href="/api/subscriptions/">Subscriptions</a></li>
        <li><a href="/api/global-settings/">Global Settings</a></li>
        <li><a href="/api/audit-logs/">Audit Logs</a></li>
        <li><a href="/api/roles/">Roles</a></li>
        <li><a href="/api/permissions/">Permissions</a></li>
        <li><a href="/api/user-roles/">User Roles</a></li>
        <li><a href="/api/users/">Users</a></li>
    </ul>
    <p>For API documentation, visit <a href="/api/">/api/</a> and explore the browsable interface.</p>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounting.urls')),
    path('', home_view),
]