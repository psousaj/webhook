# Generated by Django 4.2 on 2023-05-24 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0006_alter_messagecontrol_retries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messagecontrol',
            name='period',
            field=models.CharField(),
        ),
    ]