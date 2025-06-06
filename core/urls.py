"""
URL configuration for social_auth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('jet/', include('jet.urls', 'jet')),
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='dashboard/home.html'), name='home'),
    path('login', TemplateView.as_view(template_name='account/login.html'), name='login'),
    path('social-auth/', include('social_django.urls')),  # Thêm dòng này để tích hợp các URL của social_django
    path('accounts/', include('allauth.urls')),
    path('customrAccounts/', include('account_linking.urls')),
    path('home/', include('passport.urls')),
    path('dashboard/', include('dashboard.urls')),
    
]
