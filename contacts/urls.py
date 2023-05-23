from django.urls import path
from contacts.views import ContactViewSet

urlpatterns = [
    path('', ContactViewSet.as_view({'get': 'list'}), name='list_contacts'),
    path('/create', ContactViewSet.as_view(
        {'post': 'create'}), name='create_contacts'),
]
