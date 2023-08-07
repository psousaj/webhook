from django.urls import include, path
from webhook.routers.custom import CustomDefaultRouter
from messages_api.views import (
    MessageViewSet,
    TicketViewSet,
    update_ticket,
    update_message,
)

router = CustomDefaultRouter()
router.register(r"/list", MessageViewSet, basename="messages")
# router.register(r'/tickets', MessageViewSet, basename="tickets")

urlpatterns = [
    path("", include(router.urls)),
    path("/tickets", TicketViewSet.as_view({"get": "list"}), name="tickets"),
    path(
        "/tickets/status",
        TicketViewSet.as_view({"get": "status"}),
        name="ticket_status",
    ),
    path("/create", MessageViewSet.as_view({"post": "create"})),
    path("/update", update_message, name="update_message"),
    path("/create/ticket", TicketViewSet.as_view({"post": "create"})),
    path("/update/ticket", update_ticket, name="update_ticket"),
]
