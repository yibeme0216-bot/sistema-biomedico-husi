import json
from django import forms

from .models import RoundEntry, SurgeryRound


class RoundEntryForm(forms.ModelForm):
    sin_novedad = forms.BooleanField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = RoundEntry
        fields = [
            "categoria",
            "subservicio",
            "hallazgo",
            "placa_equipo",
            "orden_trabajo",
            "tiene_eventos_seguridad",
            "eventos_seguridad",
            "fuera_de_servicio",
            "nombre_encargado_servicio",
            "firma_servicio",
            "nombre_encargado_ronda",
            "firma_ronda",
            "sin_novedad",
        ]
        widgets = {
            "categoria": forms.HiddenInput(),
            "subservicio": forms.HiddenInput(),
            "hallazgo": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "placa_equipo": forms.TextInput(attrs={"class": "form-control"}),
            "orden_trabajo": forms.TextInput(attrs={"class": "form-control"}),
            "tiene_eventos_seguridad": forms.RadioSelect(choices=[(True, 'Sí'), (False, 'No')]),
            "eventos_seguridad": forms.Textarea(attrs={"rows": 2, "class": "form-control", "disabled": True}),
            "fuera_de_servicio": forms.TextInput(attrs={"class": "form-control"}),
            "nombre_encargado_servicio": forms.TextInput(attrs={"class": "form-control"}),
            "firma_servicio": forms.TextInput(attrs={"type": "hidden"}),  
            "nombre_encargado_ronda": forms.TextInput(attrs={"class": "form-control"}),
            "firma_ronda": forms.TextInput(attrs={"type": "hidden"}),     
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Solo validamos firmas si no es "sin novedad"
        sin_novedad = cleaned_data.get('sin_novedad', False)
        if not sin_novedad:
            nombre_servicio = cleaned_data.get('nombre_encargado_servicio')
            nombre_ronda = cleaned_data.get('nombre_encargado_ronda')
            
            # Validar nombres requeridos
            if not nombre_servicio:
                self.add_error('nombre_encargado_servicio', 'Este campo es requerido.')
            if not nombre_ronda:
                self.add_error('nombre_encargado_ronda', 'Este campo es requerido.')
        
        return cleaned_data

    def save(self, commit=True):
        instancia = super().save(commit=False)
        if instancia.sin_novedad:
            instancia.hallazgo = instancia.hallazgo or "Sin novedad"
            instancia.placa_equipo = instancia.placa_equipo or "Sin novedad"
            instancia.orden_trabajo = instancia.orden_trabajo or ""
            instancia.eventos_seguridad = instancia.eventos_seguridad or "Sin novedad"
        if commit:
            instancia.save()
        return instancia


class SurgeryRoundForm(forms.Form):
    semana_inicio = forms.DateField(
        label="Semana (lunes)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    observaciones = forms.CharField(
        label="Observaciones generales",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    nombre_encargado_servicio = forms.CharField(
        label="Nombre encargado del servicio",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    nombre_encargado_ronda = forms.CharField(
        label="Nombre encargado de la ronda", 
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    firma_servicio = forms.CharField(
        label="Firma encargado del servicio",
        widget=forms.HiddenInput(),
    )
    firma_ronda = forms.CharField(
        label="Firma encargado de la ronda",
        widget=forms.HiddenInput(),
    )
    payload = forms.CharField(widget=forms.HiddenInput())

    def clean_semana_inicio(self):
        semana = self.cleaned_data["semana_inicio"]
        if semana.weekday() != 0:
            raise forms.ValidationError("Seleccione el lunes correspondiente a la semana.")
        return semana

    def clean_payload(self):
        raw_payload = self.cleaned_data["payload"]
        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError as exc:  # pragma: no cover - validaciones de JSON
            raise forms.ValidationError("No se pudo interpretar la información del formato.") from exc

        if not isinstance(data, dict):
            raise forms.ValidationError("El formato recibido es inválido.")
        return data

    def guardar(self, usuario):
        from .utils import base64_to_image_file
        
        # Procesar firmas desde base64
        firma_servicio_file = None
        firma_ronda_file = None
        
        firma_servicio_b64 = self.cleaned_data["firma_servicio"]
        if firma_servicio_b64:
            firma_servicio_file = base64_to_image_file(firma_servicio_b64, "firma_servicio")
        
        firma_ronda_b64 = self.cleaned_data["firma_ronda"]
        if firma_ronda_b64:
            firma_ronda_file = base64_to_image_file(firma_ronda_b64, "firma_ronda")
        
        registro = SurgeryRound.objects.create(
            usuario=usuario,
            semana_inicio=self.cleaned_data["semana_inicio"],
            observaciones=self.cleaned_data.get("observaciones", ""),
            nombre_encargado_servicio=self.cleaned_data["nombre_encargado_servicio"],
            nombre_encargado_ronda=self.cleaned_data["nombre_encargado_ronda"],
            datos=self.cleaned_data["payload"],
        )
        
        # Asignar archivos de firma si se procesaron correctamente
        if firma_servicio_file:
            registro.firma_servicio = firma_servicio_file
        if firma_ronda_file:
            registro.firma_ronda = firma_ronda_file
        
        registro.save()
        return registro


class DailySurgeryRoundForm(forms.Form):
    """Formulario para registros diarios de cirugía por sala y equipo"""
    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control", "readonly": True}),
    )
    dia_semana = forms.CharField(
        label="Día de la semana",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": True}),
    )
    sala = forms.CharField(
        label="Sala",
        max_length=10,
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": True}),
    )
    equipo = forms.CharField(
        label="Equipo",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "readonly": True}),
    )
    equipo_en_uso = forms.BooleanField(
        label="¿El equipo está en uso?",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "onchange": "toggleEquipoFields(this)"}),
    )
    estado_equipo = forms.ChoiceField(
        label="Estado del equipo",
        choices=[
            ("", "-- Seleccionar --"),
            ("operativo_completo", "✅ Operativo completo"),
            ("operativo_parcial", "⚠️ Operativo parcial"),
            ("fuera_de_servicio", "❌ Fuera de servicio"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    nombre_encargado_servicio = forms.CharField(
        label="Nombre encargado del servicio",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    nombre_encargado_ronda = forms.CharField(
        label="Nombre encargado de la ronda", 
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    firma_servicio = forms.CharField(
        label="Firma encargado del servicio",
        required=False,
        widget=forms.HiddenInput(),
    )
    firma_ronda = forms.CharField(
        label="Firma encargado de la ronda",
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        cleaned_data = super().clean()
        equipo_en_uso = cleaned_data.get('equipo_en_uso')
        
        if equipo_en_uso:
            # Si el equipo está en uso, los demás campos son requeridos
            estado_equipo = cleaned_data.get('estado_equipo')
            nombre_servicio = cleaned_data.get('nombre_encargado_servicio')
            nombre_ronda = cleaned_data.get('nombre_encargado_ronda')
            
            if not estado_equipo:
                raise forms.ValidationError("Debe seleccionar el estado del equipo cuando está en uso.")
            if not nombre_servicio:
                raise forms.ValidationError("Debe ingresar el nombre del encargado del servicio.")
            if not nombre_ronda:
                raise forms.ValidationError("Debe ingresar el nombre del encargado de la ronda.")
        
        return cleaned_data
