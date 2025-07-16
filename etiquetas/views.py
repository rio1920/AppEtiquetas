from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .utils import Labelary, Patrones
from .models import Etiqueta, Variable
from .models import Impresora, Insumo, Rotacion

def etiqueta_png(request):
    if request.method == "POST":
        try:
            # Obtener el ZPL directamente o a través del ID de etiqueta
            if 'etiqueta_id' in request.POST:
                # Obtener la etiqueta por ID
                etiqueta_id = request.POST.get('etiqueta_id')
                etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
                
                # Si se proporcionó un ZPL personalizado, usarlo en lugar del almacenado
                if 'zpl_custom' in request.POST and request.POST.get('zpl_custom'):
                    zpl = request.POST.get('zpl_custom')
                else:
                    zpl = etiqueta.contenido_zpl
                
                # Si se proporcionó impresora, insumo y rotación, actualizar temporalmente
                if 'impresora_id' in request.POST and request.POST.get('impresora_id'):
                    impresora_id = request.POST.get('impresora_id')
                    impresora = get_object_or_404(Impresora, id=impresora_id)
                    etiqueta.impresora = impresora
                
                if 'insumo_id' in request.POST and request.POST.get('insumo_id'):
                    insumo_id = request.POST.get('insumo_id')
                    insumo = get_object_or_404(Insumo, id=insumo_id)
                    etiqueta.insumo = insumo
                
                if 'rotacion_id' in request.POST and request.POST.get('rotacion_id'):
                    rotacion_id = request.POST.get('rotacion_id')
                    rotacion = get_object_or_404(Rotacion, id=rotacion_id)
                    etiqueta.rotacion = rotacion
            else:
                # Modo antiguo - obtener ZPL directamente
                zpl = request.POST.get("etiqueta", "")
                etiqueta = None
                
            # Validar que el ZPL no esté vacío
            if not zpl or not zpl.strip():
                return render(request, 'etiquetas/png.html', {'error': 'El código ZPL está vacío'})
                
            # Procesar variables en el ZPL
            variables_encontradas = Patrones.extraer_variables(zpl)
            variables_en_base_datos = Variable.objects.filter(codigo__in=variables_encontradas).values('codigo', 'default')
            diccionario_variables = {var['codigo']: var['default'] for var in variables_en_base_datos}
            extrer_variables_idem_texto = Patrones.extraer_variables_de_texto(zpl)
            
            # Reemplazar variables con sus valores predeterminados
            for var in variables_encontradas:
                if var not in diccionario_variables:
                    pass  # Variable no definida
                else:
                    default_value = diccionario_variables[var]
                    for palabra in extrer_variables_idem_texto:
                        if var in palabra:
                            zpl = zpl.replace(palabra, default_value)
            
            # Si tenemos la etiqueta completa, usar el nuevo método de renderizado
            if etiqueta:
                # Actualizar el ZPL con las variables reemplazadas
                etiqueta.contenido_zpl = zpl
                labelary = Labelary()
                img = labelary.renderizar_etiqueta(etiqueta)
            else:
                # Modo antiguo - renderizar directamente el ZPL
                img = Labelary().pngPrimaria(zpl)
                
            if img:
                return render(request, 'etiquetas/png.html', {'imagen': img, 'variables': variables_encontradas})
            else:
                return render(request, 'etiquetas/png.html', {'error': 'No se pudo generar la imagen'})
        except Exception as e:

            # Logs eliminados para producción
            return render(request, 'etiquetas/png.html', {'error': f'Error al generar la etiqueta: {str(e)}'})



def index(request):
    variables = Variable.objects.values_list('codigo', flat=True)
    
    # Obtener etiquetas y agruparlas por tipo
    todas_etiquetas = Etiqueta.objects.all()
    
    # Obtener tipos únicos de etiquetas para el select
    tipos_etiquetas = [clave for clave, _ in Etiqueta.TIPO_CHOICES]
    
    # Obtener impresoras, insumos y rotaciones para los selectores
    
    impresoras = Impresora.objects.all()
    insumos = Insumo.objects.all()
    rotaciones = Rotacion.objects.all()
        
    # Obtener una etiqueta para mostrar en el textarea
    try:
        etiqueta_ejemplo = Etiqueta.objects.first()
        descripcion_zpl = etiqueta_ejemplo.contenido_zpl if etiqueta_ejemplo else ""
    except Exception:
        descripcion_zpl = ""
    
    return render(request, 'etiquetas/index.html', {
        'descripcion_zpl': descripcion_zpl,
        'variables': variables,
        'etiquetas': todas_etiquetas if todas_etiquetas else None,
        'tipos_etiquetas': tipos_etiquetas if tipos_etiquetas else None,
        'impresoras': impresoras,
        'insumos': insumos,
        'rotaciones': rotaciones,
    })

def renderizar_etiqueta(request, etiqueta_id):
    """Vista para renderizar una etiqueta específica por su ID"""
    etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
    
    # Obtener el ZPL y procesar sus variables
    zpl = etiqueta.contenido_zpl
    variables_encontradas = Patrones.extraer_variables(zpl)
    variables_en_base_datos = Variable.objects.filter(codigo__in=variables_encontradas).values('codigo', 'default')
    diccionario_variables = {var['codigo']: var['default'] for var in variables_en_base_datos}
    extrer_variables_idem_texto = Patrones.extraer_variables_de_texto(zpl)
    
    # Reemplazar variables
    for var in variables_encontradas:
        if var in diccionario_variables:
            default_value = diccionario_variables[var]
            for palabra in extrer_variables_idem_texto:
                if var in palabra:
                    zpl = zpl.replace(palabra, default_value)
    
    # Actualizar el ZPL con variables reemplazadas
    etiqueta.contenido_zpl = zpl
    
    # Renderizar usando el nuevo método
    labelary = Labelary()
    img = labelary.renderizar_etiqueta(etiqueta)
    
    return render(request, 'etiquetas/png.html', {'imagen': img, 'variables': variables_encontradas})

# Vistas para manejar el ZPL de las etiquetas
def get_zpl(request, etiqueta_id):
    """Obtiene el ZPL de una etiqueta específica y su configuración"""
    try:
        # Logs eliminados para producción
        
        etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
        
        # Validar que la etiqueta tenga todos los campos relacionados
        if not hasattr(etiqueta, 'impresora') or etiqueta.impresora is None:
            return JsonResponse({'error': 'La etiqueta no tiene impresora asignada'}, status=400)
        
        if not hasattr(etiqueta, 'insumo') or etiqueta.insumo is None:
            return JsonResponse({'error': 'La etiqueta no tiene insumo asignado'}, status=400)
            
        if not hasattr(etiqueta, 'rotacion') or etiqueta.rotacion is None:
            return JsonResponse({'error': 'La etiqueta no tiene rotación asignada'}, status=400)
        
        # Log eliminado para producción
        
        config = {
            'impresora': str(etiqueta.impresora.dpi) + ' DPI',  # Convertimos dpi a str antes de concatenar
            'insumo': etiqueta.insumo.tamanio,
            'rotacion': str(etiqueta.rotacion.angulo) + '°',
            'impresora_id': etiqueta.impresora.id,
            'insumo_id': etiqueta.insumo.id,
            'rotacion_id': etiqueta.rotacion.id,
        }
        
        return JsonResponse({
            'zpl': etiqueta.contenido_zpl,
            'config': config
        })
    except Etiqueta.DoesNotExist:
        # Log eliminado para producción
        return JsonResponse({'error': f'No se encontró la etiqueta con ID {etiqueta_id}'}, status=404)
    except Exception as e:
        # Logs eliminados para producción
        return JsonResponse({'error': f'Error al obtener la etiqueta: {str(e)}'}, status=400)

def actualizar_zpl(request):
    """Actualiza el ZPL y opcionalmente el nombre de una etiqueta en la base de datos"""
    if request.method == "POST":
        try:
            etiqueta_id = request.POST.get('etiqueta_id')
            zpl = request.POST.get('zpl')
            nombre = request.POST.get('nombre')
            
            if not etiqueta_id or not zpl:
                return JsonResponse({'success': False, 'error': 'Falta el ID de etiqueta o ZPL'}, status=400)
            
            etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
            etiqueta.contenido_zpl = zpl
            
            # Actualizar el nombre si viene en la solicitud
            if nombre:
                etiqueta.nombre = nombre
                
            etiqueta.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

def crear_etiqueta(request):
    """Vista para crear una nueva etiqueta desde la interfaz de edición manual"""
    
    if request.method == "POST":
        try:
            nombre = request.POST.get('nombre')
            tipo_etiqueta = request.POST.get('tipo_etiqueta')
            impresora_id = request.POST.get('impresora_id')
            insumo_id = request.POST.get('insumo_id')
            rotacion_id = request.POST.get('rotacion_id')
            contenido_zpl = request.POST.get('contenido_zpl')
            
            # Validar datos
            if not nombre or not tipo_etiqueta or not impresora_id or not insumo_id or not rotacion_id or not contenido_zpl:
                return JsonResponse({'success': False, 'error': 'Faltan datos obligatorios'}, status=400)
            
            # Obtener los objetos relacionados
            impresora = get_object_or_404(Impresora, id=impresora_id)
            insumo = get_object_or_404(Insumo, id=insumo_id)
            rotacion = get_object_or_404(Rotacion, id=rotacion_id)
            
            # Crear la etiqueta
            etiqueta = Etiqueta.objects.create(
                nombre=nombre,
                tipo_etiqueta=tipo_etiqueta,
                impresora=impresora,
                insumo=insumo,
                rotacion=rotacion,
                contenido_zpl=contenido_zpl
            )
            
            return JsonResponse({'success': True, 'etiqueta_id': etiqueta.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

def visualizar_etiqueta(request):
    """Vista para visualizar una etiqueta con los parámetros seleccionados sin guardarla"""
    
    if request.method == "POST":
        # Obtener datos del formulario
        impresora_id = request.POST.get('impresora_id')
        insumo_id = request.POST.get('insumo_id')
        rotacion_id = request.POST.get('rotacion_id')
        tipo_etiqueta = request.POST.get('tipo_etiqueta')
        zpl = request.POST.get('zpl')
        # Validar que tengamos los datos necesarios
        if not impresora_id or not insumo_id or not rotacion_id or not zpl:
            return render(request, 'etiquetas/png.html', {'error': 'Faltan datos obligatorios'})
        
        try:
            # Obtener objetos relacionados
            impresora = get_object_or_404(Impresora, id=impresora_id)
            insumo = get_object_or_404(Insumo, id=insumo_id)
            rotacion = get_object_or_404(Rotacion, id=rotacion_id)
            
            # Crear una etiqueta temporal (sin guardar en la base de datos)
            etiqueta = Etiqueta(
                nombre="Vista previa",
                tipo_etiqueta=tipo_etiqueta,
                impresora=impresora,
                insumo=insumo,
                rotacion=rotacion,
                contenido_zpl=zpl
            )
            
            # Procesar variables en el ZPL
            variables_encontradas = Patrones.extraer_variables(zpl)
            variables_en_base_datos = Variable.objects.filter(codigo__in=variables_encontradas).values('codigo', 'default')
            diccionario_variables = {var['codigo']: var['default'] for var in variables_en_base_datos}
            extrer_variables_idem_texto = Patrones.extraer_variables_de_texto(zpl)
            
            # Reemplazar variables con sus valores predeterminados
            for var in variables_encontradas:
                if var in diccionario_variables:
                    default_value = diccionario_variables[var]
                    for palabra in extrer_variables_idem_texto:
                        if var in palabra:
                            zpl = zpl.replace(palabra, default_value)
            
            # Actualizar el ZPL con las variables reemplazadas
            etiqueta.contenido_zpl = zpl
            
            # Renderizar usando el método correspondiente
            labelary = Labelary()
            img = labelary.renderizar_etiqueta(etiqueta)
            
            return render(request, 'etiquetas/png.html', {'imagen': img, 'variables': variables_encontradas})
        
        except Exception as e:
            return render(request, 'etiquetas/png.html', {'error': f'Error al visualizar: {str(e)}'})
    
    return render(request, 'etiquetas/png.html', {'error': 'Método no permitido'})

def actualizar_nombre_etiqueta(request):
    """Actualiza el nombre de una etiqueta existente"""
    if request.method == "POST":
        try:
            etiqueta_id = request.POST.get('etiqueta_id')
            nuevo_nombre = request.POST.get('nuevo_nombre')
            
            if not etiqueta_id or not nuevo_nombre:
                return JsonResponse({'success': False, 'error': 'Falta el ID de etiqueta o el nuevo nombre'}, status=400)
            
            etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
            etiqueta.nombre = nuevo_nombre
            etiqueta.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

def duplicar_etiqueta(request):
    """Duplica una etiqueta existente con un nuevo nombre"""
    if request.method == "POST":
        try:
            etiqueta_id = request.POST.get('etiqueta_id')
            nuevo_nombre = request.POST.get('nuevo_nombre')
            
            if not etiqueta_id or not nuevo_nombre:
                return JsonResponse({'success': False, 'error': 'Falta el ID de etiqueta o el nuevo nombre'}, status=400)
            
            # Obtener la etiqueta original
            etiqueta_original = get_object_or_404(Etiqueta, id=etiqueta_id)
            
            # Crear una nueva etiqueta con los mismos datos pero diferente nombre
            nueva_etiqueta = Etiqueta.objects.create(
                nombre=nuevo_nombre,
                tipo_etiqueta=etiqueta_original.tipo_etiqueta,
                impresora=etiqueta_original.impresora,
                insumo=etiqueta_original.insumo,
                rotacion=etiqueta_original.rotacion,
                contenido_zpl=etiqueta_original.contenido_zpl
            )
            
            return JsonResponse({'success': True, 'etiqueta_id': nueva_etiqueta.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)