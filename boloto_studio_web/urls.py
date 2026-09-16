"""
URL configuration for boloto_studio_web project.

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
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from base.views import stripe_webhook

urlpatterns = [
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
]

urlpatterns += i18n_patterns(
    path("", include("base.urls")),
    path("echoes-untamed", include("echoes_untamed.urls")),
    path("frogs/", include("frogsnet.urls")),
    path('admin/', admin.site.urls),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "images/favicon.ico"),
    ),
    path(
        "site.webmanifest",
        RedirectView.as_view(url=settings.STATIC_URL + "site.webmanifest"),
    ),
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)