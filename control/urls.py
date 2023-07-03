from django.urls import path
from control.functions import init_app, group_das_to_send
from control.views import (
    ControlMessageViewSet, 
    update_control_message, 
    send_report_to_group, 
    create_pendencies_viewset
)

urlpatterns = [
    path('', ControlMessageViewSet.as_view({'get': 'list'}), name='tickets'),
    path('/init', init_app, name='init'),
    path('/report/send-message', send_report_to_group, name='send-message-group'),
    path('/create/competence', create_pendencies_viewset, name='create-competence'),
    path('/create', ControlMessageViewSet.as_view({'post': 'create'})),
    path('/update', update_control_message, name='update_message'),
    path('/report/group-das', group_das_to_send, name='verify_grouping_of_das'),
]
