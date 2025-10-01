from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST

from django.utils import timezone
from datetime import datetime
try:
    import openpyxl
except ImportError:
    openpyxl = None
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None
from django.http import HttpResponse
from django.template.loader import render_to_string

from .forms import RoundEntryForm, SurgeryRoundForm, DailySurgeryRoundForm
from .models import RoundEntry, SurgeryRound, DailySurgeryRecord


@login_required
@permission_required('rondas.delete_roundentry', raise_exception=True)
@require_POST
def eliminar_registro(request, registro_id):
    """Vista para eliminar un registro de ronda (solo administradores)"""
    try:
        registro = get_object_or_404(RoundEntry, id=registro_id)
        nombre_registro = f"{registro.get_categoria_display()} - {registro.subservicio}"
        registro.delete()
        
        messages.success(request, f"Registro '{nombre_registro}' eliminado correctamente.")
        return JsonResponse({'success': True, 'message': 'Registro eliminado correctamente'})
    except Exception as e:
        messages.error(request, f"Error al eliminar el registro: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required('rondas.delete_surgeryround', raise_exception=True)
@require_POST
def eliminar_registro_cirugia(request, registro_id):
    """Vista para eliminar un registro de cirugía (solo administradores)"""
    try:
        registro = get_object_or_404(SurgeryRound, id=registro_id)
        fecha_registro = registro.semana_inicio.strftime('%d/%m/%Y')
        registro.delete()
        
        messages.success(request, f"Registro de cirugía del {fecha_registro} eliminado correctamente.")
        return JsonResponse({'success': True, 'message': 'Registro de cirugía eliminado correctamente'})
    except Exception as e:
        messages.error(request, f"Error al eliminar el registro de cirugía: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required('rondas.view_roundentry', raise_exception=True)
def exportar_historial_excel(request):   openpyxl = None
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None
from django.http import HttpResponse
from django.template.loader import render_to_string

from .forms import RoundEntryForm, SurgeryRoundForm, DailySurgeryRoundForm
from .models import RoundEntry, SurgeryRound, DailySurgeryRecord

PRIORITARIOS = [
    "UNIDAD DE RECIÉN NACIDOS (CUIDADOS INTERMEDIOS)",
    "UNIDAD DE RECIÉN NACIDOS (CUIDADOS INTENSIVOS)",
    "UNIDAD DE CUIDADOS INTENSIVOS",
    "UNIDAD DE CUIDADO INTENSIVO PEDIÁTRICO",
]
SEDES_EXTERNAS = [
    "Cuidados Paliativos",
    "Calle 41",
    "Intelectus",
]
def surgery_available_today(day):
    """Verifica si las salas de cirugía están disponibles hoy"""
    return day in SURGERY_AVAILABLE_DAYS

def get_services_by_day(day):
    # Servicios disponibles por día
    ronda_diaria = {
        0: ["Urgencias", "Salud Mental", "Trasplante de Médula"],
        1: ["Oftalmología", "Neurociencias", "Patología", "Radiología", "Hospitalización Aislamiento", "Sexto Centro", "Medicina Nuclear"],
        2: ["Urgencias", "Oncología", "Hemato-Oncología", "Gastroenterología"],
        3: ["Neumología", "Nefrología", "Cardiología", "Medicina Interna", "Neurología", "Otorrino"],
        4: ["Urgencias", "Consulta Externa", "Pediatría", "9 Piso"],
    }
    servicio_salas = {
        0: ["Hospitalización Cirugía", "Lactario", "Central de Esterilización", "SIPE"],
        2: ["Central de Esterilización", "Neurociencias", "SIPE"],
        4: ["Central de Esterilización", "SIPE"],
    }
    laboratorio_clinico = {
        0: [
            "LC - ALMACÉN", "LC - MICROBIOLOGÍA", "LC - BIOLOGÍA MOLECULAR", "LC - CITOMETRÍA DE FLUJO",
            "LC - INMUNOLOGÍA", "LC - HEMATOLOGÍA", "LC - QUÍMICA", "LC - TAMIZAJE",
            "LC - REFERENCIA Y CONTRAREFERENCIA", "LC - SERVICIO TRANSFUSIONAL", "LC - TOMA DE MUESTRAS", "LC - ERRORES INNATOS"
        ]
    }
    
    # Servicios disponibles para el día actual
    servicios_del_dia = {
        "ronda_diaria": ronda_diaria.get(day, []),
        "servicio_salas": servicio_salas.get(day, []),
        "laboratorio_clinico": laboratorio_clinico.get(day, []) if day == 0 else [],
        "surgery_available": surgery_available_today(day),
    }
    
    # Agregar todos los servicios disponibles (para mostrar opciones)
    todos_ronda_diaria = set()
    todos_servicio_salas = set()
    for servicios_dia in ronda_diaria.values():
        todos_ronda_diaria.update(servicios_dia)
    for servicios_dia in servicio_salas.values():
        todos_servicio_salas.update(servicios_dia)
    
    servicios_del_dia["todos_ronda_diaria"] = sorted(list(todos_ronda_diaria))
    servicios_del_dia["todos_servicio_salas"] = sorted(list(todos_servicio_salas))
    servicios_del_dia["todos_laboratorio_clinico"] = laboratorio_clinico[0]
    
    return servicios_del_dia

SURGERY_ROOMS = [str(numero) for numero in range(1, 15)]
SURGERY_EQUIPMENT = [
    "Máquina",
    "Presión bala de oxígeno (O₂)",
    "Monitor",
    "Mesa",
    "Lámpara",
    "Electrobisturí",
    "Microscopio",
    "Otros",
]
SURGERY_DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

# Días en que aparecen las salas de cirugía (0=Lunes, 1=Martes, etc.)
SURGERY_AVAILABLE_DAYS = [0, 1, 2, 3, 4, 5]  # Lunes a Sábado

# Estructura de categorías para las rondas
ROUND_STRUCTURE = {
    "prioritarios": {
        "titulo": "Servicios Prioritarios",
        "descripcion": "Servicios prioritarios siempre disponibles"
    },
    "ronda_diaria": {
        "titulo": "Ronda Diaria",
        "descripcion": "Servicios de ronda diaria según día de la semana"
    },
    "servicio_salas": {
        "titulo": "Servicio de Salas", 
        "descripcion": "Servicios dependientes del día"
    },
    "laboratorio_clinico": {
        "titulo": "Laboratorio Clínico",
        "descripcion": "Solo disponible los lunes"
    },
    "sedes_externas": {
        "titulo": "Sedes Externas",
        "descripcion": "Siempre disponibles"
    },
}

SPANISH_WEEKDAYS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


def logout_redirect(request):
    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    logout(request)
    return redirect("http://127.0.0.1:8000/")


def horario_valido(moment) -> bool:
    hour = moment.hour
    minute = moment.minute
    return (7 <= hour <= 23) or hour == 0


@login_required
def panel_principal(request):
    ahora = timezone.localtime()
    if not horario_valido(ahora):
        return render(request, "rondas/fuera_horario.html", {"ahora": ahora})

    dia_actual = SPANISH_WEEKDAYS[ahora.weekday()]
    day = ahora.weekday()
    servicios = get_services_by_day(day)

    # Formularios y lógica original
    posted_key: tuple[str, str] | None = None
    posted_form: RoundEntryForm | None = None
    if request.method == "POST":
        tipo_formulario = request.POST.get("tipo_formulario")
        if tipo_formulario == "ronda":
            print(f"DEBUG - Procesando formulario de ronda")
            print(f"DEBUG - POST data keys: {list(request.POST.keys())}")
            print(f"DEBUG - POST data: {dict(request.POST)}")
            
            from .utils import process_signature_data
            
            posted_key = (
                request.POST.get("categoria", ""),
                request.POST.get("subservicio", ""),
            )
            
            print(f"DEBUG - Posted key: {posted_key}")
            
            from .utils import base64_to_image_file
            
            # Crear formulario normal
            round_form = RoundEntryForm(request.POST)
            print(f"DEBUG - Formulario válido?: {round_form.is_valid()}")
            if not round_form.is_valid():
                print(f"DEBUG - Errores del formulario: {round_form.errors}")
            
            if round_form.is_valid():
                registro = round_form.save(commit=False)
                registro.usuario = request.user
                print(f"DEBUG - Usuario: {request.user}")
                print(f"DEBUG - Datos del registro antes de firmas: categoria={registro.categoria}, subservicio={registro.subservicio}")
                
                # Las firmas ya están guardadas en el formulario como base64
                print(f"DEBUG - Firma servicio guardada: {len(registro.firma_servicio) if registro.firma_servicio else 0} caracteres")
                print(f"DEBUG - Firma ronda guardada: {len(registro.firma_ronda) if registro.firma_ronda else 0} caracteres")
                
                try:
                    registro.save()
                    print(f"DEBUG - Registro guardado con ID: {registro.id}")
                    messages.success(request, "Registro guardado correctamente.")
                    return redirect("panel_principal")
                except Exception as e:
                    print(f"DEBUG - Error al guardar: {str(e)}")
                    messages.error(request, f"Error al guardar: {str(e)}")
            else:
                print(f"DEBUG - El formulario no es válido")
                messages.error(request, "Por favor, corrija los errores en el formulario.")
            posted_form = round_form
        elif tipo_formulario == "cirugia":
            print(f"DEBUG - Procesando formulario de cirugía...")
            print(f"DEBUG - Datos POST: {request.POST}")
            surgery_form = SurgeryRoundForm(request.POST)
            print(f"DEBUG - Formulario creado, validando...")
            if surgery_form.is_valid():
                print(f"DEBUG - Formulario válido, guardando...")
                try:
                    resultado = surgery_form.guardar(request.user)
                    print(f"DEBUG - Guardado exitoso: {resultado}")
                    messages.success(request, "Formato semanal de salas de cirugía guardado.")
                    return redirect("panel_principal")
                except Exception as e:
                    print(f"DEBUG - Error al guardar formulario de cirugía: {str(e)}")
                    messages.error(request, f"Error al guardar: {str(e)}")
            else:
                print(f"DEBUG - Formulario de cirugía NO válido")
                print(f"DEBUG - Errores: {surgery_form.errors}")
                messages.error(request, "Por favor, corrija los errores en el formulario de cirugía.")
        else:
            print(f"DEBUG - Tipo de formulario no reconocido: {tipo_formulario}")
            messages.error(request, "No se pudo identificar el formulario enviado.")

    # Salas de cirugía (solo día actual)
    surgery_layout = []
    surgery_form = None
    current_day_name = None
    
    if servicios.get("surgery_available", False):
        # Obtener el nombre del día actual en español
        current_day_name = SURGERY_DAYS[datetime.now().weekday()]
        print(f"DEBUG - Día actual para cirugía: {current_day_name}")
        
        # Solo mostrar salas para el día actual
        for sala in SURGERY_ROOMS:
            equipos = [
                equipo
                for equipo in SURGERY_EQUIPMENT
                if not (equipo == "Microscopio" and sala != "1")
            ]
            surgery_layout.append({"sala": sala, "equipos": equipos})
        surgery_form = SurgeryRoundForm()

    # Crear estructura de categorías para el template
    categories = []
    
    # Servicios prioritarios (siempre disponibles)
    if PRIORITARIOS:
        prioritarios_forms = []
        for servicio in PRIORITARIOS:
            form_key = ("prioritarios", servicio)
            form = RoundEntryForm(initial={"categoria": "prioritarios", "subservicio": servicio})
            if posted_key == form_key and posted_form:
                form = posted_form
            prioritarios_forms.append({"nombre": servicio, "form": form})
        
        categories.append({
            "clave": "prioritarios",
            "titulo": "🚨 Servicios Prioritarios (Siempre disponibles)",
            "subservicios": prioritarios_forms
        })
    
    # Rondas diarias (según día)
    if servicios.get("ronda_diaria"):
        ronda_diaria_forms = []
        for servicio in servicios["ronda_diaria"]:
            form_key = ("ronda_diaria", servicio)
            form = RoundEntryForm(initial={"categoria": "ronda_diaria", "subservicio": servicio})
            if posted_key == form_key and posted_form:
                form = posted_form
            ronda_diaria_forms.append({"nombre": servicio, "form": form})
        
        categories.append({
            "clave": "ronda_diaria",
            "titulo": f"📅 Ronda Diaria - {dia_actual}",
            "subservicios": ronda_diaria_forms
        })
    
    # Servicios de salas (según día)
    if servicios.get("servicio_salas"):
        servicio_salas_forms = []
        for servicio in servicios["servicio_salas"]:
            form_key = ("servicio_salas", servicio)
            form = RoundEntryForm(initial={"categoria": "servicio_salas", "subservicio": servicio})
            if posted_key == form_key and posted_form:
                form = posted_form
            servicio_salas_forms.append({"nombre": servicio, "form": form})
        
        categories.append({
            "clave": "servicio_salas",
            "titulo": f"🏥 Servicio de Salas - {dia_actual}",
            "subservicios": servicio_salas_forms
        })
    
    # Laboratorio clínico (solo lunes)
    if servicios.get("laboratorio_clinico"):
        lab_forms = []
        for servicio in servicios["laboratorio_clinico"]:
            form_key = ("laboratorio_clinico", servicio)
            form = RoundEntryForm(initial={"categoria": "laboratorio_clinico", "subservicio": servicio})
            if posted_key == form_key and posted_form:
                form = posted_form
            lab_forms.append({"nombre": servicio, "form": form})
        
        categories.append({
            "clave": "laboratorio_clinico",
            "titulo": "🧪 Laboratorio Clínico (Solo Lunes)",
            "subservicios": lab_forms
        })
    
    # Sedes externas (siempre disponibles)
    if SEDES_EXTERNAS:
        sedes_forms = []
        for servicio in SEDES_EXTERNAS:
            form_key = ("sedes_externas", servicio)
            form = RoundEntryForm(initial={"categoria": "sedes_externas", "subservicio": servicio})
            if posted_key == form_key and posted_form:
                form = posted_form
            sedes_forms.append({"nombre": servicio, "form": form})
        
        categories.append({
            "clave": "sedes_externas",
            "titulo": "🏢 Sedes Externas (Siempre disponibles)",
            "subservicios": sedes_forms
        })

    contexto = {
        "dia_actual": dia_actual,
        "ahora": ahora,
        "categories": categories,
        "surgery_days": [current_day_name] if current_day_name else [],
        "current_day_name": current_day_name,
        "surgery_layout": surgery_layout,
        "surgery_form": surgery_form,
        "surgery_available": servicios.get("surgery_available", False) and day in SURGERY_AVAILABLE_DAYS,
        "surgery_available_days": [SPANISH_WEEKDAYS[day] for day in SURGERY_AVAILABLE_DAYS],
    }
    return render(request, "rondas/panel.html", contexto)


@login_required
def historial_servicios(request):
    from itertools import chain
    from operator import attrgetter
    
    # Obtener registros de servicios
    registros_servicios = RoundEntry.objects.select_related("usuario")
    categoria = request.GET.get("categoria")
    if categoria:
        registros_servicios = registros_servicios.filter(categoria=categoria)
    subservicio = request.GET.get("subservicio")
    if subservicio:
        registros_servicios = registros_servicios.filter(subservicio__icontains=subservicio)
    
    # Obtener registros de cirugías
    registros_cirugias = SurgeryRound.objects.select_related("usuario")
    
    # Combinar ambos tipos de registros y ordenar por fecha
    registros_combinados = list(chain(registros_servicios, registros_cirugias))
    registros = sorted(registros_combinados, key=attrgetter('fecha_creacion'), reverse=True)

    # Agregar categorías adicionales que no están en ROUND_STRUCTURE
    categorias_completas = ROUND_STRUCTURE.copy()
    categorias_completas["prioritarios"] = {
        "titulo": "Servicios Prioritarios",
        "descripcion": "Servicios críticos siempre disponibles"
    }
    categorias_completas["sedes_externas"] = {
        "titulo": "Sedes Externas", 
        "descripcion": "Servicios en sedes externas"
    }
    categorias_completas["cirugia"] = {
        "titulo": "Cirugías",
        "descripcion": "Registros de rondas de cirugía"
    }
    
    return render(
        request,
        "rondas/historial.html",
        {
            "registros": registros,
            "categorias": categorias_completas,
        },
    )


@login_required
def indicadores(request):
    totales = list(
        RoundEntry.objects.values("categoria")
        .annotate(total=Count("id"), con_novedad=Count("id", filter=Q(sin_novedad=False)))
        .order_by("categoria")
    )

    sin_novedad = {
        item["categoria"]: item["total"]
        for item in RoundEntry.objects.filter(sin_novedad=True)
        .values("categoria")
        .annotate(total=Count("id"))
    }

    resumen = [
        {
            "clave": item["categoria"],
            "titulo": ROUND_STRUCTURE.get(item["categoria"], {}).get("titulo", item["categoria"].title()),
            "total": item["total"],
            "con_novedad": item["con_novedad"],
            "sin_novedad": sin_novedad.get(item["categoria"], 0),
        }
        for item in totales
    ]

    # Indicadores adicionales
    equipos_fuera_servicio = RoundEntry.objects.filter(
        fuera_de_servicio=True
    ).count()
    
    eventos_seguridad = RoundEntry.objects.filter(
        tiene_eventos_seguridad=True
    ).count()
    
    # Top 5 servicios con más equipos fuera de servicio
    top_fuera_servicio = list(
        RoundEntry.objects.filter(fuera_de_servicio=True)
        .values("subservicio", "categoria")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )
    
    # Top 5 servicios con más eventos de seguridad
    top_eventos_seguridad = list(
        RoundEntry.objects.filter(tiene_eventos_seguridad=True)
        .values("subservicio", "categoria")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    semanal_cirugia = (
        SurgeryRound.objects.values("semana_inicio")
        .annotate(total=Count("id"))
        .order_by("-semana_inicio")[:12]
    )

    return render(
        request,
        "rondas/indicadores.html",
        {
            "resumen": resumen,
            "semanal_cirugia": semanal_cirugia,
            "equipos_fuera_servicio": equipos_fuera_servicio,
            "eventos_seguridad": eventos_seguridad,
            "top_fuera_servicio": top_fuera_servicio,
            "top_eventos_seguridad": top_eventos_seguridad,
        },
    )


@login_required
@permission_required('rondas.view_roundentry', raise_exception=True)
def exportar_historial_pdf(request):
    # Obtener registros regulares
    registros = RoundEntry.objects.select_related("usuario")
    categoria = request.GET.get("categoria")
    if categoria:
        registros = registros.filter(categoria=categoria)
    subservicio = request.GET.get("subservicio")
    if subservicio:
        registros = registros.filter(subservicio__icontains=subservicio)
    
    # Obtener registros de cirugía
    registros_cirugia = SurgeryRound.objects.select_related("usuario").order_by("-fecha_creacion")
    if pisa is None:
        # Si no está xhtml2pdf, descarga un TXT con los datos
        contenido = "Fecha\tCategoría\tServicio\tHallazgo\tEventos\tPlaca\tOrden\tNombre Encargado Servicio\tFirma Servicio\tNombre Encargado Ronda\tFirma Ronda\tEstado\n"
        for r in registros:
            eventos_seg_text = 'Sí: ' + r.eventos_seguridad if r.tiene_eventos_seguridad and r.eventos_seguridad else ('Sí' if r.tiene_eventos_seguridad else 'No')
            contenido += f"{r.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\t{r.get_categoria_display()}\t{r.subservicio}\t{r.hallazgo}\t{eventos_seg_text}\t{r.placa_equipo}\t{r.orden_trabajo}\t{getattr(r, 'nombre_encargado_servicio', '')}\t{r.firma_servicio}\t{getattr(r, 'nombre_encargado_ronda', '')}\t{r.firma_ronda}\t{'Sin novedad' if r.sin_novedad else 'Con novedad'}\n"
        response = HttpResponse(contenido, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename=historial.txt'
        return response
    html = render_to_string("rondas/historial_pdf.html", {
        "registros": registros,
        "registros_cirugia": registros_cirugia
    })
    response = HttpResponse(content_type="application/pdf")
    pisa.CreatePDF(html, dest=response)
    return response


@login_required
@permission_required('rondas.view_roundentry', raise_exception=True)
def exportar_historial_excel(request):
    registros = RoundEntry.objects.select_related("usuario")
    categoria = request.GET.get("categoria")
    if categoria:
        registros = registros.filter(categoria=categoria)
    subservicio = request.GET.get("subservicio")
    if subservicio:
        registros = registros.filter(subservicio__icontains=subservicio)
    if openpyxl is None:
        # Si no está openpyxl, descarga un TXT con los datos
        contenido = "Fecha\tCategoría\tServicio\tHallazgo\tEventos\tPlaca\tOrden\tNombre Encargado Servicio\tFirma Servicio\tNombre Encargado Ronda\tFirma Ronda\tEstado\n"
        for r in registros:
            contenido += f"{r.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\t{r.get_categoria_display()}\t{r.subservicio}\t{r.hallazgo}\t{r.eventos_seguridad}\t{r.placa_equipo}\t{r.orden_trabajo}\t{getattr(r, 'nombre_encargado_servicio', '')}\t{r.firma_servicio}\t{getattr(r, 'nombre_encargado_ronda', '')}\t{r.firma_ronda}\t{'Sin novedad' if r.sin_novedad else 'Con novedad'}\n"
        response = HttpResponse(contenido, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename=historial.txt'
        return response
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Fecha", "Categoría", "Servicio", "Hallazgo", "Eventos", "Placa", "Orden", "Nombre Encargado Servicio", "Tiene Firma Servicio", "Nombre Encargado Ronda", "Tiene Firma Ronda", "Estado"])
    for r in registros:
        ws.append([
            r.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
            r.get_categoria_display(),
            r.subservicio,
            r.hallazgo,
            'Sí: ' + r.eventos_seguridad if r.tiene_eventos_seguridad and r.eventos_seguridad else ('Sí' if r.tiene_eventos_seguridad else 'No'),
            r.placa_equipo,
            r.orden_trabajo,
            getattr(r, 'nombre_encargado_servicio', ''),
            "Sí" if r.firma_servicio else "No",
            getattr(r, 'nombre_encargado_ronda', ''),
            "Sí" if r.firma_ronda else "No",
            "Sin novedad" if r.sin_novedad else "Con novedad"
        ])
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename=historial.xlsx'
    wb.save(response)
    return response


