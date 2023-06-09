# Generated by Django 2.2.28 on 2023-07-03 17:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0003_auto_20230703_1738'),
        ('control', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DASFileGrouping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.DateField()),
                ('companies', models.ManyToManyField(to='contacts.CompanyContact')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='das_file_grouping', to='contacts.Contact')),
            ],
        ),
    ]
