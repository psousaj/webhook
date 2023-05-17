from rest_framework.routers import SimpleRouter
from messages_api.views import MessageViewSet

from django.urls import include, path

router = SimpleRouter()
router.urls.append(path('', MessageViewSet.as_view(), name='today'))

urlpatterns = [
    path('message', include(router.urls))
]
