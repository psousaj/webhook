from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.http import Http404
from django.shortcuts import get_object_or_404

# Create your models here.

class Contact(models.Model):
    contact_id = models.CharField(max_length=255, primary_key=True)
    country_code = models.CharField(max_length=3)
    ddd = models.CharField(max_length=2)
    contact_number = models.CharField(max_length=9)
    company_contacts = models.ManyToManyField(
        "CompanyContact",
        related_name="digisac_contacts",
        blank=True,
    )
    establishments = ArrayField(models.IntegerField(), null=True, blank=True) #Works only with PostGresSQL

    def __str__(self) -> str:
        return f"{self.contact_number} - {self.company_contact.first()}"

    def append_new_contact(self, new_contact: "CompanyContact"):
        self.company_contacts.add(new_contact)

    def append_new_establishment(self, new_establishment: int):
        if not self.establishments:
            self.establishments = []
        if new_establishment not in self.establishments:
            self.establishments.append(new_establishment)
        self.save()

    class Meta:
        unique_together = (('contact_number', 'contact_id'),)

class CompanyContact(models.Model):
    cnpj = models.CharField(max_length=14, unique=True)
    company_name = models.CharField(max_length=255)
    responsible_name = models.CharField(max_length=255)
    establishment_id = models.IntegerField(null=True, blank=True)
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="company_contact",
        null=True,
        blank=False,
    )  

    class Meta:
        unique_together = (('cnpj', 'establishment_id'),)

    def __str__(self) -> str:
        return f"{self.company_name} - {self.cnpj}: {self.responsible_name.upper()}"

    def get_or_create_contact(self, **kwargs):
        contact, created = Contact.objects.get_or_create(**kwargs)

        self.contact = contact
        self.save()

        return self.contact

    def get_pendencies(self):
        return self.pendencies.all()

    def get_contact_number(self):
        return self.contact.contact_number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.contact:
            self.contact.save()

class Pendencies(models.Model):
    contact = models.ForeignKey(CompanyContact, on_delete=models.CASCADE, related_name='pendencies')
    cnpj = models.CharField(max_length=255)
    period = models.DateField()
    pdf = models.TextField()
