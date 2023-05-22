from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from messages_api.models import Message


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
