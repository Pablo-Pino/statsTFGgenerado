# Generated by Django 3.0.2 on 2020-03-13 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websecurityapp', '0010_sesionactividad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sesionactividad',
            name='token',
            field=models.CharField(max_length=100),
        ),
    ]
