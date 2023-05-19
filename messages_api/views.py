from datetime import datetime as dt
from rest_framework import viewsets
from django.db import IntegrityError
from django.forms import ValidationError
from django.http.request import HttpRequest
from rest_framework.response import Response
from rest_framework.decorators import api_view

from webhook.logger import Logger
from messages_api.models import Message
from messages_api.exceptions import NotFoundException
from messages_api.serializer import MessageSerializer

# Create your views here.
logger = Logger(__name__)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    http_method_names = ['get', 'post', 'put', 'patch']

    def get_queryset(self):
        queryset = Message.objects.all()
        period = self.request.query_params.get('period')
        cnpj = self.request.query_params.get('cnpj')
        month = self.request.query_params.get('month')

        if period:
            try:
                if len(period) == 5:
                    period = '20' + period[-2:] + '-' + period[:2] + '-01'
                    dt.strptime(period, '%Y-%m-%d')
            except ValueError:
                raise NotFoundException(
                    'Invalid period format, should be YYYY-MM-DD or MM-YY.')
            except ValidationError:
                raise NotFoundException(
                    'Invalid date format! try to switch "-" to "/"')

            if len(period) == 5:
                period = dt.now().strftime(
                    '%Y-') + period[-2:] + '-' + period[:2] + ' 00:00:00'

            try:
                # parsed_period = datetime.strptime(period, '%Y-%m-%d').date()
                if queryset.filter(period=period).exists():
                    queryset = queryset.filter(period=period)
                else:
                    raise NotFoundException(
                        "No obligation found for this period.")
            except ValueError:
                raise NotFoundException(
                    "Invalid period format, should be YYYY-MM-DD or MM-YY BLÉ")

        elif month and not cnpj:
            try:
                month_int = int(month)
                if not queryset.filter(period__month=month_int).exists():
                    raise NotFoundException("None Message for this month")
                elif month_int > 0 and month_int <= 12 and queryset.filter(period__month=month_int).exists():
                    queryset = queryset.filter(period__month=month_int)
            except ValueError:
                raise NotFoundException(
                    "Invalid month, should be an integer between 1 and 12")

        elif cnpj and not month and not period:
            if queryset.filter(cnpj_base=cnpj).exists():
                queryset = queryset.filter(cnpj_base=cnpj)
            else:
                raise NotFoundException("None obligation for this cnpj")

        if cnpj and period:
            try:
                parsed_period = dt.strptime(period, '%Y-%m-%d').date()
                if queryset.filter(period=parsed_period, cnpj_base=cnpj).exists():
                    queryset = queryset.filter(
                        period=parsed_period, cnpj_base=cnpj)
                else:
                    raise NotFoundException(
                        "None obligation found for the specified parameters.")
            except ValueError:
                raise NotFoundException(
                    "Invalid period format, should be YYYY-MM-DD.")

        if cnpj and month:
            try:
                try:
                    month_int = int(month)
                    if not queryset.filter(period__month=month_int).exists():
                        raise NotFoundException(
                            "None Message for this month")
                    elif not queryset.filter(cnpj_base=cnpj).exists():
                        raise NotFoundException("CNPJ does not exists")
                    elif not queryset.filter(period__month=month_int, cnpj_base=cnpj).exists():
                        raise NotFoundException(
                            "None Message in this month for the specified cnpj")
                except ValueError:
                    raise NotFoundException(
                        "Invalid month, should be an integer between 1 and 12")

                if queryset.filter(period__month=month_int, cnpj_base=cnpj).exists():
                    queryset = queryset.filter(
                        period__month=month_int, cnpj_base=cnpj)
            except ValueError:
                raise NotFoundException("Internal Error")

        return queryset

    def create(self, request, *args, **kwargs):
        contact_number = request.query_params.get('contact')
        period = request.query_params.get('period')
        contact_id = request.data.get('contact_id')
        status = request.data.get('status')
        message_id = request.data.get('message_id')
        ticket_id = request.data.get('ticket_id')
        message_type = request.data.get('type')

        if not contact_number:
            return Response({'error': 'You must provide a phone_number query parameters.'}, status=400)
        if not period:
            return Response({'error': 'You must provide period query parameters.'}, status=400)
        if not contact_id or not status or not message_id or not ticket_id or not message_type:
            return Response(
                {
                    'error': 'You must provide all body fields.',
                    'fields': ["contact_id", "status", "message_id", "ticket_id", "message_type"]
                }, status=400)

        try:
            if len(period) == 5:
                period = '20' + period[-2:] + '-' + period[:2] + '-01'
            dt.strptime(period, '%Y-%m-%d')
        except ValueError:
            return Response({'error': 'Invalid period format, should be YYYY-MM-DD or MM-YY.'}, status=400)

        if len(period) == 5:
            period = dt.now().strftime(
                '%Y-') + period[-2:] + '-' + period[:2] + ' 00:00:00'
        try:
            message = Message.objects.create(
                contact_id=contact_id,
                contact_number=contact_number,
                period=period,
                status=status,
                message_id=message_id,
                ticket_service_id=ticket_id,
                message_type=message_type,
                retries=0
            )
        except (IntegrityError, TypeError) as e:
            error_code, error_msg = e.args
            text = str(error_msg)
            logger.debug(f"{text}")
            return Response({f"error {error_code}": "Something Wrong", "message": text}, status=409)

        # obligation_control =
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=201)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)

            if not queryset:
                return Response({"no_content": "There are no yet messages to show"}, status=200)

            return Response(serializer.data)
        except NotFoundException as e:
            return Response({'error': str(e)}, status=404)

    def up_obligation(self, request, cnpj_base, period):
        try:
            if len(period) == 5:
                period = '20' + period[-2:] + '-' + period[:2] + '-01'
            dt.strptime(period, '%Y-%m-%d')
        except ValueError:
            return Response({'error': 'Invalid period format, should be YYYY-MM-DD or MM-YY.'}, status=400)

        if len(period) == 5:
            period = dt.now().strftime(
                '%Y-') + period[-2:] + '-' + period[:2] + ' 00:00:00'

        try:
            message = Message.objects.get(
                cnpj_base=cnpj_base, period=period)
        except Message.DoesNotExist:
            raise Exception({'error': 'Message not found.'})

        # Verifica se os campos passados na requisição existem na Model
        serializer = MessageSerializer(message)
        fields = serializer.get_fields()
        # for field in request.data.keys():
        #     if field not in fields:
        #         raise Exception({'error': f'Invalid field: {field}', 'fields_available': [
        #             'download_json_das', 'downloads_das', 'verify_das_mei_data', 'sent_das_file']})

        for field in request.data.keys():
            if field not in fields:
                return Response({'error': 'Invalid field in request.', 'fields_available': [
                    'download_json_das', 'downloads_das', 'verify_das_mei_data', 'sent_das_file']}, status=400)

        # Atualiza a obrigação com os valores da requisição
        serializer = MessageSerializer(
            message, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(
                download_json_das=request.data.get(
                    'download_json_das', message.download_json_das),
                download_das=request.data.get(
                    'download_das', message.download_das),
                verify_das_mei_data=request.data.get(
                    'verify_das_mei_data', message.verify_das_mei_data),
                sent_das_file=request.data.get(
                    'sent_das_file', message.notify_current_das)
            )
            logger.info(f"Message for {message.cnpj_base} updated")
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)


@api_view(['PATCH'])
def update_message(request: HttpRequest):
    cnpj_base = request.query_params.get('cnpj')
    period = request.query_params.get('period')
    view = MessageViewSet()

    try:
        return view.up_obligation(request, cnpj_base=cnpj_base, period=period)
    except Exception as e:
        raise Exception(e)
