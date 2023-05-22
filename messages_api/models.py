from django.db import models


class Ticket(models.Model):
    ticket_id = models.CharField(max_length=255, primary_key=True)
    period = models.DateTimeField()

    @property
    def messages(self):
        return list(self.message_set.values('message_id', 'text', 'status'))

    @property
    def message_count(self):
        return len(self.messages)


class Message(models.Model):
    message_id = models.CharField(max_length=255, primary_key=True)
    contact_id = models.CharField(max_length=255, null=False)
    contact_number = models.CharField(max_length=255, null=False)
    period = models.DateField()
    timestamp = models.DateTimeField(default=None)
    status = models.IntegerField(
        choices=((0, 'Criada'), (1, 'Enviada'), (2, 'Recebida'), (3, 'Visualizada')))
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=255)
    is_from_me = models.BooleanField(default=False)
    text = models.CharField(max_length=255)
    retries = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.contact_number} - {self.period} - {self.status}"

    class Meta:
        unique_together = (('contact_id', 'message_id', 'status'),)
