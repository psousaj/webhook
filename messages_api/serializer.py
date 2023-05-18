from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from messages_api.models import Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        # fields = '__all__'
        exclude = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Message.objects.all(),
                fields=['cnpj_cpf', 'period']
            )
        ]
