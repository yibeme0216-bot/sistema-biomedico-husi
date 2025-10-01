# Generated manually for SurgeryRound model updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rondas', '0002_service_roundentry_fuera_de_servicio_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='surgeryround',
            name='observaciones',
            field=models.TextField(blank=True, verbose_name='Observaciones generales'),
        ),
        migrations.AddField(
            model_name='surgeryround',
            name='nombre_encargado_servicio',
            field=models.CharField(default='Sin especificar', max_length=100),
        ),
        migrations.AddField(
            model_name='surgeryround',
            name='nombre_encargado_ronda',
            field=models.CharField(default='Sin especificar', max_length=100),
        ),
    ]