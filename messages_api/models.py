from django.db import models

# Create your models here.


class Message(models.Model):
    contact_id = models.CharField(max_length=255, null=False)
    contact_number = models.CharField(max_length=255, null=False)
    period = models.DateField()
    status = models.IntegerField(
        choices=((1, 'Enviada'), (2, 'Recebida'), (3, 'Visualizada')))
    message_id = models.CharField(max_length=255)
    ticket_service_id = models.CharField(max_length=255)
    message_type = models.CharField(max_length=255)
    retries = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.contact_id} - {self.period} - {self.status}"

    class Meta:
        unique_together = (('contact_id', 'message_id'),)
