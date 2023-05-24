# Generated by Django 4.2 on 2023-05-24 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('contact_id', models.CharField(primary_key=True, serialize=False)),
                ('cnpj', models.CharField(max_length=255)),
                ('id_establishment', models.CharField(max_length=255)),
                ('country_code', models.CharField()),
                ('ddd', models.CharField()),
                ('contact_number', models.CharField()),
            ],
            options={
                'unique_together': {('cnpj', 'contact_id')},
            },
        ),
    ]
