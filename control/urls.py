from django.urls import path
from control.views import ControlMessageViewSet, update_control_message
from control.functions import init_app

urlpatterns = [
    path('', ControlMessageViewSet.as_view({'get': 'list'}), name='tickets'),
    path('/init', init_app, name='init'),
    path('/create', ControlMessageViewSet.as_view({'post': 'create'})),
    path('/update', update_control_message, name='update_message'),
]
