from django.contrib import admin

from control.models import MessageControl, TicketLink, DASFileGrouping

# Register your models here.
admin.site.register(MessageControl)
admin.site.register(TicketLink)
admin.site.register(DASFileGrouping)
