from django.db import models

# Create your models here.


class Contact(models.Model):
    contact_id = models.CharField(max_length=255, primary_key=True)
    cnpj = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, default='RAZÃO SOCIAL...')
    id_establishment = models.CharField(max_length=255)
    country_code = models.CharField(max_length=255)
    ddd = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.contact_number} - {self.cnpj} - {self.contact_id}"

    def get_pendencies(self):
        return self.pendencies.all()

    class Meta:
        unique_together = (('cnpj', 'contact_id'),)


class Pendencies(models.Model):
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name='pendencies')
    cnpj = models.CharField(max_length=255)
    period = models.DateField()
    pdf = models.TextField()
