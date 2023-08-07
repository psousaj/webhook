# Generated by Django 4.2.1 on 2023-07-27 16:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Ticket",
            fields=[
                (
                    "ticket_id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("period", models.DateField()),
                ("is_open", models.BooleanField(default=True)),
                ("contact_id", models.CharField(max_length=255)),
                (
                    "last_message_id",
                    models.CharField(default="ndsaujfbnujsafbncuj", max_length=500),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                (
                    "message_id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("contact_id", models.CharField(max_length=255)),
                ("contact_number", models.CharField(max_length=255)),
                ("period", models.DateField()),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (0, "Criada"),
                            (1, "Enviada"),
                            (2, "Recebida"),
                            (3, "Visualizada"),
                        ]
                    ),
                ),
                ("message_type", models.CharField(max_length=255)),
                ("is_from_me", models.BooleanField(default=False)),
                ("text", models.CharField(max_length=500)),
                ("retries", models.IntegerField(default=0)),
                (
                    "ticket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="messages_api.ticket",
                    ),
                ),
            ],
            options={
                "unique_together": {("contact_id", "message_id", "status")},
            },
        ),
    ]
