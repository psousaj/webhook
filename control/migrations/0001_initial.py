# Generated by Django 4.2.1 on 2023-07-27 16:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contacts", "0001_initial"),
        ("messages_api", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageControl",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("pendencies", models.BooleanField(default=False)),
                ("contact", models.CharField(max_length=255)),
                ("period", models.DateField()),
                (
                    "status",
                    models.IntegerField(
                        choices=[(0, "Aguardando Resposta"), (1, "Fechado")], default=0
                    ),
                ),
                ("client_needs_help", models.BooleanField(default=False)),
                ("retries", models.IntegerField(default=1)),
                (
                    "ticket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ticket",
                        to="messages_api.ticket",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TicketLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "additional_tickets",
                    models.ManyToManyField(
                        blank=True, related_name="ticketlinks", to="messages_api.ticket"
                    ),
                ),
                (
                    "last_ticket",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="last_ticketlink",
                        to="messages_api.ticket",
                    ),
                ),
                (
                    "message_control",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="control.messagecontrol",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DASFileGrouping",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("period", models.DateField()),
                (
                    "companies",
                    models.ManyToManyField(blank=True, to="contacts.companycontact"),
                ),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="das_file_grouping",
                        to="contacts.contact",
                    ),
                ),
            ],
        ),
    ]
