from django.urls import path
from control.views import ControlMessageViewSet, update_control_message, send_report_to_group, create_pendencies_viewset
from control.functions import init_app, check_client_response_viewset

urlpatterns = [
    path('', ControlMessageViewSet.as_view({'get': 'list'}), name='tickets'),
    path('/init', init_app, name='init'),
    path('/report/send-message', send_report_to_group, name='send-message-group'),
    path('/check_response', check_client_response_viewset, name='check_response'),
    path('/create/competence', create_pendencies_viewset, name='create-competence'),
    path('/create', ControlMessageViewSet.as_view({'post': 'create'})),
    path('/update', update_control_message, name='update_message'),
]
