from rest_framework import serializers
from control.models import MessageControl, TicketLink
from messages_api.serializer import TicketSerializer


class TicketLinkSerializer(serializers.ModelSerializer):
    additional_tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = TicketLink
        fields = "__all__"


class ControlMessageSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer(read_only=True)
    ticket_link = TicketLinkSerializer(read_only=True)

    class Meta:
        model = MessageControl
        fields = "__all__"
