from django.db import models

# Create your models here.


class Contact(models.Model):
    contact_id = models.CharField(primary_key=True)
    cnpj = models.CharField(max_length=255)
    id_establishment = models.CharField(max_length=255)
    country_code = models.CharField()
    ddd = models.CharField()
    contact_number = models.CharField()

    def __str__(self) -> str:
        return f"{self.cnpj} - {self.cnpj} - {self.contact_id}"

    class Meta:
        unique_together = (('cnpj', 'contact_id'),)
