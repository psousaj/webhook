from django.urls import include, path
from webhook.routers.custom import CustomDefaultRouter
from messages_api.views import MessageViewSet, update_message

router = CustomDefaultRouter()
router.register(r'', MessageViewSet, basename="messages")

urlpatterns = [
    path('', include(router.urls)),
    path('/create', MessageViewSet.as_view({'post': 'create'})),
    path('/update', update_message, name='update_message'),
]
