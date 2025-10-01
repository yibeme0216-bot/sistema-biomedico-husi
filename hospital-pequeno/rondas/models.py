from django.conf import settings
from django.db import models


class RoundEntry(models.Model):
    """Registro de rondas para servicios generales."""

    CATEGORIAS = [
        ("prioritarios", "Prioritarios"),
        ("ronda_diaria", "Ronda diaria"),
        ("servicio_salas", "Servicio de salas"),
        ("laboratorio_clinico", "Laboratorio clínico"),
        ("sedes_externas", "Sedes externas"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rondas_registradas",
    )
    categoria = models.CharField(max_length=32, choices=CATEGORIAS)
    subservicio = models.CharField(max_length=100)
    hallazgo = models.TextField(blank=True)
    placa_equipo = models.CharField(max_length=100, blank=True)
    orden_trabajo = models.CharField(max_length=100, blank=True)
    tiene_eventos_seguridad = models.BooleanField(default=False, verbose_name="¿Hay eventos de seguridad?")
    eventos_seguridad = models.TextField(blank=True, verbose_name="Descripción de eventos de seguridad")
    fuera_de_servicio = models.CharField(max_length=200, blank=True)
    nombre_encargado_servicio = models.CharField(max_length=100, default='Sin especificar')
    firma_servicio = models.TextField(blank=True, null=True, verbose_name="Firma del encargado del servicio")
    nombre_encargado_ronda = models.CharField(max_length=100, default='Sin especificar')
    firma_ronda = models.TextField(blank=True, null=True, verbose_name="Firma del encargado de la ronda")
    sin_novedad = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Registro de ronda"
        verbose_name_plural = "Registros de rondas"

    def __str__(self) -> str:  # pragma: no cover - representación legible
        return f"{self.get_categoria_display()} - {self.subservicio}"


class SurgeryRound(models.Model):
    """Formato semanal de salas de cirugía."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="formatos_cirugia",
    )
    semana_inicio = models.DateField(
        help_text="Fecha correspondiente al lunes de la semana registrada.",
    )
    datos = models.JSONField()
    observaciones = models.TextField(blank=True, verbose_name="Observaciones generales")
    nombre_encargado_servicio = models.CharField(max_length=100, default='Sin especificar')
    nombre_encargado_ronda = models.CharField(max_length=100, default='Sin especificar')
    firma_servicio = models.TextField(
        blank=True, null=True, verbose_name="Firma del encargado del servicio"
    )
    firma_ronda = models.TextField(
        blank=True, null=True, verbose_name="Firma del encargado de la ronda"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "Ronda de cirugía"
        verbose_name_plural = "Rondas de cirugía"

    def __str__(self) -> str:  # pragma: no cover - representación legible
        return f"Semana {self.semana_inicio}"


class Service(models.Model):
    """Servicios del hospital."""
    CATEGORIAS = [
        ("PRIORITARIO", "Prioritario"),
        ("DIARIA", "Ronda diaria"),
        ("SALAS", "Servicio de salas"),
        ("LAB", "Laboratorio clínico"),
        ("SEDES", "Sedes externas"),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIAS)
    day_rules = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
    
    def __str__(self):
        return self.name


class Room(models.Model):
    """Salas o habitaciones."""
    TIPOS = [
        ("sala_cirugia", "Sala de cirugía"),
        ("habitacion", "Habitación"),
        ("consulta", "Consulta"),
        ("laboratorio", "Laboratorio"),
        ("otro", "Otro"),
    ]
    
    number = models.CharField(max_length=50)
    name = models.CharField(max_length=200, blank=True)
    room_type = models.CharField(max_length=20, choices=TIPOS, default="otro")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="rooms")
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
    
    def __str__(self):
        return f"{self.number} - {self.name or self.service.name}"


class Equipment(models.Model):
    """Equipos médicos."""
    ESTADOS = [
        ("operativo_completo", "Operativo completo"),
        ("operativo_parcial", "Operativo parcial"),
        ("fuera_de_servicio", "Fuera de servicio"),
    ]
    
    name = models.CharField(max_length=200)
    plate_number = models.CharField(max_length=100, blank=True, verbose_name="Placa")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="equipments", null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="equipments")
    status = models.CharField(max_length=20, choices=ESTADOS, default="operativo_completo")
    tags = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
    
    def __str__(self):
        return f"{self.name} - {self.plate_number or 'Sin placa'}"


class DailySurgeryRecord(models.Model):
    """Registro diario de equipos de cirugía"""
    ESTADOS = [
        ("operativo_completo", "Operativo completo"),
        ("operativo_parcial", "Operativo parcial"),
        ("fuera_de_servicio", "Fuera de servicio"),
    ]
    
    usuario = models.ForeignKey("auth.User", on_delete=models.CASCADE, verbose_name="Usuario")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha = models.DateField(verbose_name="Fecha del registro")
    dia_semana = models.CharField(max_length=20, verbose_name="Día de la semana")
    sala = models.CharField(max_length=10, verbose_name="Sala")
    equipo = models.CharField(max_length=100, verbose_name="Equipo")
    equipo_en_uso = models.BooleanField(default=True, verbose_name="Equipo en uso")
    estado_equipo = models.CharField(max_length=20, choices=ESTADOS, blank=True, null=True, verbose_name="Estado del equipo")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    nombre_encargado_servicio = models.CharField(max_length=100, blank=True, verbose_name="Encargado del servicio")
    nombre_encargado_ronda = models.CharField(max_length=100, blank=True, verbose_name="Encargado de la ronda")
    firma_servicio = models.TextField(blank=True, verbose_name="Firma del encargado del servicio")
    firma_ronda = models.TextField(blank=True, verbose_name="Firma del encargado de la ronda")
    
    class Meta:
        verbose_name = "Registro Diario de Cirugía"
        verbose_name_plural = "Registros Diarios de Cirugía"
        unique_together = [["fecha", "sala", "equipo"]]  # Un registro por día, sala y equipo
        ordering = ["-fecha_creacion"]
    
    def __str__(self):
        return f"{self.fecha} - Sala {self.sala} - {self.equipo}"
