import base64
import io
import uuid
from django.core.files.base import ContentFile
from PIL import Image


def base64_to_image_file(base64_string, filename_prefix="firma"):
    """
    Convierte una imagen base64 a un archivo Django que puede ser guardado en ImageField
    """
    if not base64_string or not base64_string.startswith('data:image'):
        return None
    
    try:
        # Extraer el formato y los datos
        format_info, base64_data = base64_string.split(';base64,')
        image_format = format_info.split('/')[-1].lower()
        
        # Decodificar base64
        image_data = base64.b64decode(base64_data)
        
        # Crear archivo en memoria
        image_io = io.BytesIO(image_data)
        
        # Abrir con PIL para procesar
        image = Image.open(image_io)
        
        # Convertir a RGB si es necesario (para PNG con transparencia)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Crear fondo blanco
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Redimensionar si es muy grande (máximo 800x600)
        max_size = (800, 600)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Guardar en BytesIO como JPEG para reducir tamaño
        output_io = io.BytesIO()
        image.save(output_io, format='JPEG', quality=85, optimize=True)
        output_io.seek(0)
        
        # Crear archivo Django
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.jpg"
        django_file = ContentFile(output_io.getvalue(), name=filename)
        
        return django_file
        
    except Exception as e:
        print(f"Error procesando imagen base64: {e}")
        return None


def process_signature_data(form_data):
    """
    Procesa los datos de firma del formulario y convierte base64 a archivos
    """
    processed_data = form_data.copy()
    
    # Procesar firma del servicio
    if 'firma_servicio' in processed_data and processed_data['firma_servicio']:
        firma_servicio_file = base64_to_image_file(
            processed_data['firma_servicio'], 
            "firma_servicio"
        )
        if firma_servicio_file:
            processed_data['firma_servicio'] = firma_servicio_file
    
    # Procesar firma de la ronda
    if 'firma_ronda' in processed_data and processed_data['firma_ronda']:
        firma_ronda_file = base64_to_image_file(
            processed_data['firma_ronda'], 
            "firma_ronda"
        )
        if firma_ronda_file:
            processed_data['firma_ronda'] = firma_ronda_file
    
    return processed_data