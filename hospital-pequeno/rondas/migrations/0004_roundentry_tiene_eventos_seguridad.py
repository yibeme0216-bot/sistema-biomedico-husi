# Generated manually for tiene_eventos_seguridad field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rondas', '0003_surgeryround_fields_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='roundentry',
            name='tiene_eventos_seguridad',
            field=models.BooleanField(default=False, verbose_name='¿Hay eventos de seguridad?'),
        ),
        migrations.AlterField(
            model_name='roundentry',
            name='eventos_seguridad',
            field=models.TextField(blank=True, verbose_name='Descripción de eventos de seguridad'),
        ),
    ]