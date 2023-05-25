from datetime import datetime as dt
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from django.db import IntegrityError
from django.forms import ValidationError
from django.http.request import HttpRequest
from rest_framework.response import Response
from rest_framework.decorators import api_view

from webhook.logger import Logger
from messages_api.models import Message, Ticket
from control.models import MessageControl
from control.serializer import ControlMessageSerializer
from contacts.models import Contact
from messages_api.exceptions import NotFoundException
from messages_api.serializer import MessageSerializer, TicketSerializer, TicketStatusSerializer

# Create your views here.
logger = Logger(__name__)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    http_method_names = ['get', 'post', 'put', 'patch']

    def get_queryset(self):
        queryset = Message.objects.all()
        message_id = self.request.query_params.get('id')
        period = self.request.query_params.get('period')
        status = self.request.query_params.get('status')

        if message_id:
            queryset = queryset.filter(message_id=message_id)
        if status:
            queryset = queryset.filter(status=status)
        # if period:
        #     try:
        #         if len(period) == 5:
        #             period = '20' + period[-2:] + '-' + period[:2] + '-01'
        #             dt.strptime(period, '%Y-%m-%d')
        #     except ValueError:
        #         raise NotFoundException(
        #             'Invalid period format, should be YYYY-MM-DD or MM-YY.')
        #     except ValidationError:
        #         raise NotFoundException(
        #             'Invalid date format! try to switch "-" to "/"')

        #     if len(period) == 5:
        #         period = dt.now().strftime(
        #             '%Y-') + period[-2:] + '-' + period[:2] + ' 00:00:00'

        #     try:
        #         # parsed_period = datetime.strptime(period, '%Y-%m-%d').date()
        #         if queryset.filter(period=period).exists():
        #             queryset = queryset.filter(period=period)
        #         else:
        #             raise NotFoundException(
        #                 "No obligation found for this period.")
        #     except ValueError:
        #         raise NotFoundException(
        #             "Invalid period format, should be YYYY-MM-DD or MM-YY BLÉ")

        # if status and not message_id:
        #     try:
        #         month_int = int(status)
        #         if not queryset.filter(period__month=month_int).exists():
        #             raise NotFoundException("None Message for this month")
        #         elif month_int > 0 and month_int <= 12 and queryset.filter(period__month=month_int).exists():
        #             queryset = queryset.filter(period__month=month_int)
        #     except ValueError:
        #         raise NotFoundException(
        #             "Invalid month, should be an integer between 1 and 12")

        # elif message_id and not status and not period:
        #     if queryset.filter(cnpj_base=message_id).exists():
        #         queryset = queryset.filter(cnpj_base=message_id)
        #     else:
        #         raise NotFoundException("None obligation for this cnpj")

        # elif message_id and period:
        #     try:
        #         parsed_period = dt.strptime(period, '%Y-%m-%d').date()
        #         if queryset.filter(period=parsed_period, cnpj_base=message_id).exists():
        #             queryset = queryset.filter(
        #                 period=parsed_period, cnpj_base=message_id)
        #         else:
        #             raise NotFoundException(
        #                 "None obligation found for the specified parameters.")
        #     except ValueError:
        #         raise NotFoundException(
        #             "Invalid period format, should be YYYY-MM-DD.")

        # elif message_id and status:
        #     try:
        #         try:
        #             month_int = int(status)
        #             if not queryset.filter(period__month=month_int).exists():
        #                 raise NotFoundException(
        #                     "None Message for this month")
        #             elif not queryset.filter(cnpj_base=message_id).exists():
        #                 raise NotFoundException("CNPJ does not exists")
        #             elif not queryset.filter(period__month=month_int, cnpj_base=message_id).exists():
        #                 raise NotFoundException(
        #                     "None Message in this month for the specified cnpj")
        #         except ValueError:
        #             raise NotFoundException(
        #                 "Invalid month, should be an integer between 1 and 12")

        #         if queryset.filter(period__month=month_int, cnpj_base=message_id).exists():
        #             queryset = queryset.filter(
        #                 period__month=month_int, cnpj_base=message_id)
        #     except ValueError:
        #         raise NotFoundException("Internal Error")

        return queryset

    def create(self, request, *args, **kwargs):
        contact_number = request.query_params.get('phone')
        period = request.query_params.get('period')
        timestamp = request.data.get('timestamp')
        contact_id = request.data.get('contact_id')
        status = request.data.get('status')
        message_id = request.data.get('message_id')
        ticket_id = request.data.get('ticket')
        ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
        message_type = request.data.get('message_type')
        isFromMe = request.data.get('is_from_me')
        text = request.data.get('text')

        if not contact_number:
            return Response({'error': 'You must provide a phone_number query parameters.'}, status=400)
        if not period:
            return Response({'error': 'You must provide period query parameters.'}, status=400)
        if not contact_id or status is None or not message_id or not ticket or not message_type:
            return Response(
                {
                    'error': 'You must provide all body fields.',
                    'fields': [
                        "contact_id" if not contact_id else "",
                        "status" if not status else "",
                        "message_id" if not message_id else "",
                        "ticket" if not ticket else "",
                        "message_type" if not message_type else ""
                    ]
                }, status=400)

        try:
            if len(period) == 5:
                period = '20' + period[-2:] + '-' + period[:2] + '-01'
            dt.strptime(period, '%Y-%m-%d')
        except ValueError:
            return Response({'error': 'Invalid period format, should be YYYY-MM-DD or MM-YY.'}, status=400)

        if len(period) == 5:
            period = dt.now().strftime(
                '%Y-') + period[-2:] + '-' + period[:2]
        try:
            message = Message.objects.create(
                contact_id=contact_id,
                contact_number=contact_number,
                period=period,
                timestamp=timestamp,
                status=status,
                message_id=message_id,
                ticket=ticket,
                message_type=message_type,
                is_from_me=isFromMe,
                text=text,
                retries=0
            )
        except (IntegrityError, TypeError) as e:
            text = str(e)
            logger.debug(f"{text}")
            return Response({f"error": "Something Wrong", "message": text}, status=409)

        # obligation_control =
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=201)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(
                self.get_queryset())  # self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            if not queryset:
                return Response({"no_content": "There are no yet messages to show"}, status=404)

            return Response(serializer.data)
        except NotFoundException as e:
            return Response({'error': str(e)}, status=500)

    def up_message(self, request, **kwargs):
        message = Message.objects.get(message_id=kwargs['message_id'])
        if message:
            serializer = MessageSerializer(message)
            serializer = MessageSerializer(
                message, data={'status': kwargs['status']}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)

            return Response({"erro": serializer.errors}, status=400)

        text = f"Update message_id: {kwargs['message_id']} failed"
        logger.debug(text)
        return text


@api_view(['PATCH'])
def update_message(request: HttpRequest):
    message_id = request.query_params.get('id')
    status = request.query_params.get('status')
    view = MessageViewSet()

    try:
        return view.up_message(request, message_id=message_id, status=status)
    except NotFoundException:
        return Response({'error': 400, 'message': "Mensagem não encontrada"}, status=400)
    except Exception as e:
        return Response({'error': 400, 'message': str(e)}, status=400)


class TicketViewSet(viewsets.ModelViewSet):
    # queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    http_method_names = ['get', 'post', 'put', 'patch']

    def get_queryset(self):
        ticket_id = self.request.query_params.get('id')
        queryset = Ticket.objects.all()

        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)

        return queryset

    def create(self, request, *args, **kwargs):
        ticket_id = request.query_params.get('id')
        period = request.query_params.get('period')
        contact_id = request.query_params.get('contact')
        last_message_id = request.query_params.get('last_message')

        if not contact_id:
            return Response({'error': 'You must provide a contact id query parameter.'}, status=400)
        if not ticket_id:
            return Response({'error': 'You must provide a ticket id query parameter.'}, status=400)
        if not period:
            return Response({'error': 'You must provide a period query parameter.'}, status=400)

        try:
            if len(period) == 5:
                period = '20' + period[-2:] + '-' + period[:2] + '-01'
            dt.strptime(period, '%Y-%m-%d')
        except ValueError:
            return Response({'error': 'Invalid period format, should be YYYY-MM-DD or MM-YY.'}, status=400)

        if len(period) == 5:
            period = dt.now().strftime(
                '%Y-') + period[-2:] + '-' + period[:2]

        try:
            message = Ticket.objects.create(
                ticket_id=ticket_id,
                period=period,
                contact_id=contact_id,
                last_message_id=last_message_id
            )
            contact = get_object_or_404(Contact, contact_id=contact_id)
            control_message = MessageControl.objects.create(
                ticket=get_object_or_404(Ticket, ticket_id=ticket_id),
                contact=contact.contact_number,
                period=period
            )
        except (IntegrityError, TypeError) as e:
            # error_code, error_msg = e.args
            text = str(e)
            logger.debug(f"{text}")
            return Response({f"error {e}": "Something Wrong", "message": text}, status=409)

        # obligation_control =
        serializer = TicketSerializer(message)
        return Response(serializer.data, status=201)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(
                self.get_queryset())  # self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            if not queryset:
                return Response({"no_content": "There are no yet tickets to show"}, status=404)

            return Response(serializer.data)
        except NotFoundException as e:
            return Response({'error': str(e)}, status=500)

    def up_ticket(self, request, ticket_id, is_open, last_message_id):
        try:
            message = Ticket.objects.get(ticket_id=ticket_id)
            if message:
                serializer = TicketSerializer(message)
                serializer = TicketSerializer(
                    message, data={'is_open': is_open, "last_message_id": last_message_id}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({'success': 200, 'data': serializer.data}, status=200)

                return Response({"erro": serializer.errors}, status=400)
        except Exception as e:
            text = f"Update ticket: {ticket_id} failed"
            logger.debug(text)
            return Response({'error': 500, 'message': text, 'cause': str(e)}, status=500)

    def status(self, request):
        try:
            queryset = self.filter_queryset(
                self.get_queryset())
            serializer = TicketStatusSerializer(queryset, many=True)

            if not queryset:
                return Response({"no_content": "There are no yet tickets to show"}, status=200)

            return Response(serializer.data)
        except NotFoundException as e:
            return Response({'error': str(e)}, status=404)


@api_view(['PATCH'])
def update_ticket(request: HttpRequest):
    ticket_id = request.query_params.get('id')
    is_open = request.query_params.get('open')
    last_message_id = request.query_params.get('last_message')
    view = TicketViewSet()
    # try:
    return view.up_ticket(request, ticket_id, is_open, last_message_id)
    # except NotFoundException:
    #     return Response({'error': 400, 'message': "Ticket não encontrado"}, status=400)
    # except Exception as e:
    #     return Response({'error': 400, 'message': str(e)}, status=400)


@api_view(['GET'])
def get_status(request: HttpRequest):
    id = request.query_params.get('id')
    view = TicketViewSet

    return view.status(id)
