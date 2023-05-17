from django.db import models

# Create your models here.


class Messages(models.Model):
    cnpj_cpf = models.CharField(max_length=255, null=False)
    period = models.DateField()
    status = models.IntegerField(
        choices=((1, 'Enviada'), (2, 'Recebida'), (3, 'Visualizada')))
    message_id = models.CharField(max_length=255)
    ticket_service_id = models.CharField(max_length=255)
    message_type = models.CharField(max_length=255)
    retries = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.cnpj_cpf} - {self.period} - {self.status}"

    class Meta:
        unique_together = (('message_id', 'ticket_service_id'),)
