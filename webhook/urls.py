"""vercel_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from webhook.views import webhook_avaliation, webhook_receiver

urlpatterns = [
    path("admin/", admin.site.urls),
    path("webhook", webhook_receiver, name="webhook"),
    path("webhook/messages", include("messages_api.urls")),
    path("webhook/contacts", include("contacts.urls")),
    path("webhook/control", include("control.urls")),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# Adicione esta linha para servir arquivos estáticos durante o desenvolvimento
urlpatterns += staticfiles_urlpatterns()
