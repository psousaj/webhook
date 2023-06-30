from rest_framework import serializers
from contacts.models import Contact, Pendencies, CompanyContact

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'contact_id',
            'country_code',
            'ddd',
            'contact_number',
            'company_contacts',
            'establishments'
        ]

class PendenciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pendencies
        fields = ['contact', 'cnpj', 'period']

class CompanyContactSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)
    pendencies = PendenciesSerializer(read_only=True, many=True)
    class Meta:
        model = CompanyContact
        fields = [
            'cnpj',
            'establishment_id',
            'company_name',
            'responsible_name',
            'contact',
            'pendencies'
        ]

