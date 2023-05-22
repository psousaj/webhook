from django.urls import include, path
from webhook.routers.custom import CustomDefaultRouter
from messages_api.views import MessageViewSet, TicketViewSet, update_message, list_tickets

router = CustomDefaultRouter()
router.register(r'/list', MessageViewSet, basename="messages")
router.register(r'/tickets', MessageViewSet, basename="tickets")

urlpatterns = [
    path('', include(router.urls)),
    path('/create', MessageViewSet.as_view({'post': 'create'})),
    path('/create/ticket', TicketViewSet.as_view({'post': 'create'})),
    path('/ticket', list_tickets, name='list_tickets'),
    path('/update', update_message, name='update_message'),
]
