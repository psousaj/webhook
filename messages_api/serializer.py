from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from messages_api.models import Message, Ticket


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        # validators = [
        #     UniqueTogetherValidator(
        #         queryset=Message.objects.all(),
        #         fields=['contact_id', 'message_id']
        #     )
        # ]


class MessageSerializerByTicket(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['message_id', 'contact_id', 'status', 'is_from_me', 'text']


class TicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['is_open']


class TicketSerializer(serializers.ModelSerializer):
    messages = MessageSerializerByTicket(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
