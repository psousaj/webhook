from django.contrib import admin
from messages_api.models import Ticket, Message

# Register your models here.
admin.site.register(Message)
admin.site.register(Ticket)
