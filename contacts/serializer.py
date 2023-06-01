from rest_framework import serializers
from contacts.models import Contact, Pendencies


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class PendenciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pendencies
        fields = ['contact', 'cnpj', 'period']
