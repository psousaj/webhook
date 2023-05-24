from rest_framework import serializers
from control.models import MessageControl
from messages_api.serializer import TicketSerializer


class ControlMessageSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)

    class Meta:
        model = MessageControl
        fields = '__all__'
