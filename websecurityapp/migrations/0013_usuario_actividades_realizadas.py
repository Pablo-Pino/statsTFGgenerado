# Generated by Django 3.0.2 on 2020-04-05 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websecurityapp', '0012_oferta'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='actividades_realizadas',
            field=models.ManyToManyField(to='websecurityapp.Actividad'),
        ),
    ]
