from django.contrib import admin
from contacts.models import Contact, Pendencies, CompanyContact

# Register your models here.
admin.site.register(Contact)
admin.site.register(CompanyContact)
admin.site.register(Pendencies)
