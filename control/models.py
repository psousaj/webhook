from django.db import models

from messages_api.models import Ticket
# Create your models here.


class MessageControl(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="ticket")
    pendencies = models.BooleanField()
    contact = models.CharField(max_length=255)
    retries = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.contact} - {self.period} - {self.retries}"

    class Meta:
        unique_together = (('ticket', 'contact'),)
