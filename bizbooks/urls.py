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
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BizBooks API</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; margin: 0; padding: 20px; }
            h1 { color: #007bff; text-align: center; }
            h2 { color: #28a745; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 10px 0; }
            a { text-decoration: none; color: #007bff; font-weight: bold; padding: 10px; border: 1px solid #007bff; border-radius: 5px; display: inline-block; transition: background-color 0.3s; }
            a:hover { background-color: #007bff; color: white; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            .icon { margin-right: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏢 BizBooks API</h1>
            <p>Welcome to the BizBooks accounting backend for Indian GST/TDS compliance.</p>
            <h2>🚀 Quick Links</h2>
            <ul>
                <li><span class="icon">🔧</span><a href="/admin/">Admin Panel</a></li>
                <li><span class="icon">📡</span><a href="/api/">API Root (Browsable)</a></li>
                <li><span class="icon">🏢</span><a href="/api/organizations/">Organizations</a></li>
                <li><span class="icon">👥</span><a href="/api/parties/">Parties</a></li>
                <li><span class="icon">💰</span><a href="/api/tax-config/">Tax Configurations</a></li>
                <li><span class="icon">📋</span><a href="/api/plans/">Plans</a></li>
                <li><span class="icon">📅</span><a href="/api/subscriptions/">Subscriptions</a></li>
                <li><span class="icon">⚙️</span><a href="/api/global-settings/">Global Settings</a></li>
                <li><span class="icon">📝</span><a href="/api/audit-logs/">Audit Logs</a></li>
                <li><span class="icon">🛡️</span><a href="/api/roles/">Roles</a></li>
                <li><span class="icon">🔑</span><a href="/api/permissions/">Permissions</a></li>
                <li><span class="icon">👤</span><a href="/api/user-roles/">User Roles</a></li>
                <li><span class="icon">👨‍💼</span><a href="/api/users/">Users</a></li>
            </ul>
            <p>For full API documentation, visit <a href="/api/">/api/</a> and explore the interactive interface.</p>
        </div>
    </body>
    </html>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounting.urls')),
    path('', home_view),
]