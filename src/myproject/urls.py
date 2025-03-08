"""
URL configuration for myproject project.

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
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from myproject.views import HomePageRedirectView, AccountLoginView, AccountLoginConfirmationView, AccountLogoutView, \
    AccountLogoutYesNoView, AccountLogoutConfirmationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomePageRedirectView.as_view(), name='home-page'),
    path('plants/', include('plant_care.urls')),

    # LOGIN / LOGOUT
    path('login/', AccountLoginView.as_view(), name='login'),
    path('login-confirmation/', AccountLoginConfirmationView.as_view(), name='login-confirmation'),
    path('logout-confirmation/', AccountLogoutConfirmationView.as_view(), name='logout-confirmation'),
    path('logout-yes-no/', AccountLogoutYesNoView.as_view(), name='logout-yes-no'),
    path('logout/', AccountLogoutView.as_view(), name='logout'),
]
