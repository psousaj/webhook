from django.urls import path
from contacts.views import ContactViewSet, update_contact

urlpatterns = [
    path("", ContactViewSet.as_view({"get": "list"}), name="list_contacts"),
    path("/create", ContactViewSet.as_view({"post": "create"}), name="create_contacts"),
    path("/update", update_contact, name="update contact"),
]
