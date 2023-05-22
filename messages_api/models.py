import os
from django.db import models

# Create your models here.


class Message(models.Model):
    message_id = models.CharField(max_length=255, primary_key=True)
    contact_id = models.CharField(max_length=255, null=False)
    contact_number = models.CharField(max_length=255, null=False)
    period = models.DateField()
    timestamp = models.DateTimeField(default=None)
    status = models.IntegerField(
        choices=((0, 'Criada'), (1, 'Enviada'), (2, 'Recebida'), (3, 'Visualizada')))
    ticket_service_id = models.CharField(max_length=255)
    message_type = models.CharField(max_length=255)
    is_from_me = models.BooleanField(default=False)
    text = models.CharField()
    retries = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.contact_number} - {self.period} - {self.status}"

    class Meta:
        unique_together = (('contact_id', 'message_id', 'status'),)
