from datetime import datetime as dt
from django.db import IntegrityError

from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response

from contacts.serializer import ContactSerializer
from contacts.models import Contact
from webhook.logger import Logger
# Create your views here.

logger = Logger(__name__)


class ContactViewSet(viewsets.ModelViewSet):
    # queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    http_method_names = ['get', 'post', 'put', 'patch']

    def get_queryset(self):
        contact_id = self.request.query_params.get('id')
        cnpj = self.request.query_params.get('cnpj')
        contact = self.request.query_params.get('contact')
        queryset = Contact.objects.all()

        if cnpj:
            queryset = queryset.filter(cnpj=cnpj)
        if contact:
            queryset = queryset.filter(contact_number=contact)
        if contact_id:
            queryset = queryset.filter(contact_id=contact_id)

        return queryset

    def create(self, request, *args, **kwargs):
        cnpj = request.query_params.get('cnpj')
        contact_id = request.query_params.get('id')
        company_name = request.data.get('company_name')
        id_establishment = request.data.get('id_establishment')
        country_code = request.data.get('country_code')
        ddd = request.data.get('ddd')
        contact_number = request.data.get('contact_number')

        if not cnpj:
            return Response({'error': 'You must provide a CNPJ query parameter.'}, status=400)
        if not contact_id:
            return Response({'error': 'You must provide a CONTACT_ID id query parameter.'}, status=400)

        try:
            contact = Contact.objects.create(
                cnpj=cnpj,
                contact_id=contact_id,
                company_name=company_name,
                id_establishment=id_establishment,
                country_code=country_code,
                ddd=ddd,
                contact_number=contact_number
            )
        except (IntegrityError, TypeError) as e:
            error_code, error_msg = e.args
            text = str(error_msg)
            logger.debug(f"{text}")
            return Response({f"error {error_code}": "Something Wrong", "message": text}, status=409)

        # obligation_control =
        serializer = ContactSerializer(contact)
        return Response(serializer.data, status=201)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(
                self.get_queryset())  # self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            if not queryset:
                return Response({"no_content": "There are no yet contacts to show"}, status=200)

            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=404)

    def up_ticket(self, request, contact_id, is_open):
        try:
            contact = Contact.objects.get(contact_id=contact_id)
            if contact:
                serializer = ContactSerializer(contact)
                serializer = ContactSerializer(
                    contact, data={'is_open': is_open}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'success': 200, 'data': serializer.data}, status=200)

                return Response({"erro": serializer.errors}, status=400)
        except Exception as e:
            text = f"Update Contact: {contact_id} failed"
            logger.debug(text)
            return Response({'error': 500, 'message': text, 'cause': str(e)}, status=500)
