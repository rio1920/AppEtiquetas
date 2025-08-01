from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .utils import Labelary, Patrones, formatear_fecha
from .models import Etiqueta, Variable
from .models import Impresora, Insumo, Rotacion, Idioma
import re


def verificar_variables_no_definidas(variables_encontradas, variables_definidas, contexto="", info_adicional=""):
    """
    Función utilitaria para identificar variables que no están definidas en la base de datos
    y registrarlas en la consola para su seguimiento.
    
    Args:
        variables_encontradas: Lista de variables encontradas en el ZPL
        variables_definidas: Diccionario de variables definidas en la base de datos
        contexto: Nombre de la función o contexto para el log
        info_adicional: Información adicional útil para el seguimiento
    
    Returns:
        Lista de variables no definidas
    """
    variables_no_definidas = [var for var in variables_encontradas if var not in variables_definidas]
    
    if variables_no_definidas:
        print(f"[{contexto}] Variables no definidas en la base de datos: {variables_no_definidas}")
        if info_adicional:
            print(f"[{contexto}] Info adicional: {info_adicional}")
    
    return variables_no_definidas

def procesar_variables_con_idioma(zpl, idioma_default='ES'):
    """
    Procesa el ZPL para encontrar variables con idioma y reemplazarlas con los valores correspondientes.
    
    Args:
        zpl: String con el código ZPL
        idioma_default: Código del idioma por defecto si no se especifica uno (en mayúsculas)
    
    Returns:
        ZPL procesado y diccionario de variables no encontradas
    """
    # Extraer todas las variables del ZPL
    variables_encontradas = Patrones.extraer_variables(zpl)
    
    # Extraer variables con su idioma específico
    variables_con_idioma = Patrones.extraer_variables_con_idioma(zpl)
    
    # Para cada variable, buscar su valor según el idioma correspondiente
    variables_procesadas = {}
    variables_no_encontradas = {}
    
    for var in variables_encontradas:
        # Determinar el idioma para esta variable
        idioma_asignado = variables_con_idioma.get(var, idioma_default)
        
        if idioma_asignado == "MULTI_IDIOMA":
            # Esta es una variable con el formato [@Variable[@IDIOMAVARIABLE@]@]
            # Necesitamos buscar su valor en el idioma especificado en la solicitud
            try:
                variable_obj = Variable.objects.get(codigo=var, idioma=idioma_default)
                variables_procesadas[var] = variable_obj.default
            except Variable.DoesNotExist:
                variables_no_encontradas[var] = idioma_default
                variables_procesadas[var] = None
                print(f"Variable multi-idioma '{var}' no encontrada en idioma '{idioma_default}'")
        else:
            # Procesamiento normal para variables con idioma específico
            try:
                # Buscar la variable con el idioma específico
                variable_obj = Variable.objects.get(codigo=var, idioma=idioma_asignado)
                variables_procesadas[var] = variable_obj.default
            except Variable.DoesNotExist:
                try:
                    # Si no existe con ese idioma, intentar con el idioma por defecto
                    variable_obj = Variable.objects.get(codigo=var, idioma=idioma_default)
                    variables_procesadas[var] = variable_obj.default
                    print(f"Variable '{var}' no encontrada en idioma '{idioma_asignado}', usando idioma por defecto")
                except Variable.DoesNotExist:
                    variables_no_encontradas[var] = idioma_asignado
                    variables_procesadas[var] = None
                    print(f"Variable '{var}' no encontrada en ningún idioma")
    
    # Reemplazar las variables en el ZPL
    # Primero, procesar el patrón especial [@Variable[@IDIOMAVARIABLE@]@]
    patron_idioma_anidado = re.compile(r'\[@([^@\[\]]+)\[@IDIOMAVARIABLE@]@]')
    for match in patron_idioma_anidado.findall(zpl):
        var_limpia = Patrones.limpiar_variable(match)
        if var_limpia in variables_procesadas and variables_procesadas[var_limpia]:
            patron_completo = f"[@{match}[@IDIOMAVARIABLE@]@]"
            zpl = zpl.replace(patron_completo, variables_procesadas[var_limpia])
    
    # Procesar variables de fecha con formato específico
    # Patrón: [@Variable;FFdd/MM/yyyy@] o cualquier otro formato soportado
    patron_fecha = re.compile(r'\[@([^@\[\];]+);([FfDdMmYyHhSs/.-:]+)@]')
    for match in patron_fecha.findall(zpl):
        var_nombre = match[0].strip()
        formato_fecha = match[1].strip()
        var_limpia = Patrones.limpiar_variable(var_nombre)
        
        # Si encontramos el valor para la variable, intentar formatearlo como fecha
        if var_limpia in variables_procesadas and variables_procesadas[var_limpia]:
            valor = variables_procesadas[var_limpia]
            # Intentar formatear como fecha con detección automática de formato
            valor_formateado = formatear_fecha(valor, formato_fecha)
            # Reemplazar en el ZPL
            patron_completo = f"[@{var_nombre};{formato_fecha}@]"
            zpl = zpl.replace(patron_completo, valor_formateado)
            print(f"Variable de fecha '{var_limpia}' formateada según '{formato_fecha}'")
        else:
            # Si la variable no existe en la base de datos, podría ser una fecha literal
            # Intentar interpretar el nombre de la variable como una fecha literal
            try:
                valor_formateado = formatear_fecha(var_nombre, formato_fecha)
                patron_completo = f"[@{var_nombre};{formato_fecha}@]"
                zpl = zpl.replace(patron_completo, valor_formateado)
                print(f"Fecha literal '{var_nombre}' formateada según '{formato_fecha}' -> '{valor_formateado}'")
            except Exception as e:
                print(f"No se pudo interpretar '{var_nombre}' como fecha: {e}")
                
    # Procesar fechas literales fuera de variables (formato directo en el texto)
    zpl = Patrones.detectar_y_formatear_fechas_literales(zpl)
    
    # Luego procesar el resto de las variables
    extrer_variables_idem_texto = Patrones.extraer_variables_de_texto(zpl)
    
    for palabra in extrer_variables_idem_texto:
        var_limpia = Patrones.extraer_var_limpia(palabra)
        if var_limpia and var_limpia in variables_procesadas and variables_procesadas[var_limpia]:
            zpl = zpl.replace(palabra, variables_procesadas[var_limpia])
    
    return zpl, variables_no_encontradas

def etiqueta_png(request):
    # Obtener todos los idiomas para el selector
    from .models import Idioma
    idiomas = Idioma.objects.all()
    
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
                
            # Procesamiento con soporte para variables con idioma
            idioma_default = 'ES'  # Idioma por defecto (en mayúsculas)
            
            # Si hay un idioma especificado en la solicitud, usarlo
            if 'idioma' in request.POST and request.POST.get('idioma'):
                idioma_solicitado = request.POST.get('idioma')
                try:
                    # Verificar si el idioma solicitado existe en la base de datos
                    from .models import Idioma
                    Idioma.objects.get(codigo=idioma_solicitado)  # codigo es la clave primaria
                    idioma_default = idioma_solicitado
                except Exception:
                    pass  # Si el idioma no existe, se mantiene el idioma por defecto
            
            # Extraer todas las variables para mantener compatibilidad con el código existente
            variables_encontradas = Patrones.extraer_variables(zpl)
            
            # Procesar las variables con el idioma correspondiente
            zpl, variables_no_encontradas = procesar_variables_con_idioma(zpl, idioma_default)
            
            # Registrar variables no encontradas para seguimiento
            if variables_no_encontradas:
                info_adicional = f"Etiqueta ID: {etiqueta_id if 'etiqueta_id' in request.POST else 'N/A'}, Idioma: {idioma_default}"
                print(f"[etiqueta_png] Variables no encontradas: {variables_no_encontradas}")
                print(f"[etiqueta_png] Info adicional: {info_adicional}")
            
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
                return render(request, 'etiquetas/png.html', {
                    'imagen': img, 
                    'variables': variables_encontradas,
                    'idiomas': idiomas,
                    'idioma_actual': idioma_default  # Para marcar el idioma seleccionado
                })
            else:
                return render(request, 'etiquetas/png.html', {
                    'error': 'No se pudo generar la imagen',
                    'idiomas': idiomas,
                    'idioma_actual': idioma_default  # Mantener el idioma seleccionado incluso en caso de error
                })
        except Exception as e:
            # Logs eliminados para producción
            
            # Determinar el idioma actual (usar el valor por defecto si no se especificó)
            idioma_default = 'ES'
            if 'idioma' in request.POST and request.POST.get('idioma'):
                try:
                    # Verificar si el idioma solicitado existe en la base de datos
                    Idioma.objects.get(codigo=request.POST.get('idioma'))
                    idioma_default = request.POST.get('idioma')
                except Exception:
                    pass
            
            return render(request, 'etiquetas/png.html', {
                'error': f'Error al generar la etiqueta: {str(e)}',
                'idiomas': idiomas,
                'idioma_actual': idioma_default
            })



def index(request):
    variables = Variable.objects.values_list('codigo', flat=True)
    
    # Obtener etiquetas y agruparlas por tipo
    todas_etiquetas = Etiqueta.objects.all()
    
    # Obtener tipos únicos de etiquetas para el select
    tipos_etiquetas = [clave for clave, _ in Etiqueta.TIPO_CHOICES]
    
    # Obtener impresoras, insumos, rotaciones e idiomas para los selectores
    impresoras = Impresora.objects.all()
    insumos = Insumo.objects.all()
    rotaciones = Rotacion.objects.all()
    idiomas = Idioma.objects.all()  # Obtener todos los idiomas disponibles
        
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
        'idiomas': idiomas,  # Pasar los idiomas a la plantilla
    })

def renderizar_etiqueta(request, etiqueta_id):
    """Vista para renderizar una etiqueta específica por su ID"""
    # Obtener todos los idiomas para el selector
    from .models import Idioma
    idiomas = Idioma.objects.all()
    
    etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
    
    # Obtener el ZPL y procesarlo con el soporte para idiomas
    zpl = etiqueta.contenido_zpl
    
    # Extraer todas las variables para mantener compatibilidad con el código existente
    variables_encontradas = Patrones.extraer_variables(zpl)
    
    # Idioma por defecto 'ES' (español), se podría configurar como parámetro en la solicitud
    idioma_default = 'ES'
    if request.GET.get('idioma'):
        try:
            from .models import Idioma
            Idioma.objects.get(codigo=request.GET.get('idioma'))  # codigo es la clave primaria
            idioma_default = request.GET.get('idioma')
        except Exception:
            pass
            
    # Procesar las variables con el idioma correspondiente
    zpl, variables_no_encontradas = procesar_variables_con_idioma(zpl, idioma_default)
    
    # Registrar variables no encontradas para seguimiento
    if variables_no_encontradas:
        info_adicional = f"Etiqueta ID: {etiqueta_id}, Nombre: '{etiqueta.nombre}', Idioma: {idioma_default}"
        print(f"[renderizar_etiqueta] Variables no encontradas: {variables_no_encontradas}")
        print(f"[renderizar_etiqueta] Info adicional: {info_adicional}")
    
    # Actualizar el ZPL con variables reemplazadas
    etiqueta.contenido_zpl = zpl
    
    # Renderizar usando el nuevo método
    labelary = Labelary()
    img = labelary.renderizar_etiqueta(etiqueta)
    
    return render(request, 'etiquetas/png.html', {
        'imagen': img, 
        'variables': variables_encontradas,
        'idiomas': idiomas,
        'idioma_actual': idioma_default  # Para marcar el idioma seleccionado
    })

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
                # Verificar si ya existe otra etiqueta con el mismo nombre y tipo (excluyendo esta misma)
                if Etiqueta.objects.filter(nombre=nombre, tipo_etiqueta=etiqueta.tipo_etiqueta).exclude(id=etiqueta_id).exists():
                    return JsonResponse({
                        'success': False, 
                        'error': f'Ya existe otra etiqueta con el nombre "{nombre}" para el tipo "{etiqueta.tipo_etiqueta}".',
                        'errorType': 'duplicate'
                    }, status=400)
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
            
            # Verificar si ya existe una etiqueta con el mismo nombre y tipo
            if Etiqueta.objects.filter(nombre=nombre, tipo_etiqueta=tipo_etiqueta).exists():
                return JsonResponse({
                    'success': False, 
                    'error': f'Ya existe una etiqueta con el nombre "{nombre}" para el tipo "{tipo_etiqueta}".',
                    'errorType': 'duplicate'
                }, status=400)
            
            # Obtener los objetos relacionados
            impresora = get_object_or_404(Impresora, id=impresora_id)
            insumo = get_object_or_404(Insumo, id=insumo_id)
            rotacion = get_object_or_404(Rotacion, id=rotacion_id)
            
            # Crear la etiqueta
            Etiqueta.objects.create(
                nombre=nombre,
                tipo_etiqueta=tipo_etiqueta,
                impresora=impresora,
                insumo=insumo,
                rotacion=rotacion,
                contenido_zpl=contenido_zpl
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

def visualizar_etiqueta(request):
    """Vista para visualizar una etiqueta con los parámetros seleccionados sin guardarla"""
    
    # Obtener todos los idiomas para el selector
    from .models import Idioma
    idiomas = Idioma.objects.all()
    
    if request.method == "POST":
        # Obtener datos del formulario
        impresora_id = request.POST.get('impresora_id')
        insumo_id = request.POST.get('insumo_id')
        rotacion_id = request.POST.get('rotacion_id')
        tipo_etiqueta = request.POST.get('tipo_etiqueta')
        zpl = request.POST.get('zpl')
        # Validar que tengamos los datos necesarios
        if not impresora_id or not insumo_id or not rotacion_id or not zpl:
            return render(request, 'etiquetas/png.html', {'error': 'Faltan datos obligatorios', 'idiomas': idiomas})
        
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
            
            # Extraer variables para mantener compatibilidad con código existente
            variables_encontradas = Patrones.extraer_variables(zpl)
            
            # Determinar el idioma a utilizar
            idioma_default = 'ES'  # Idioma por defecto (en mayúsculas)
            if 'idioma' in request.POST and request.POST.get('idioma'):
                try:
                    from .models import Idioma
                    Idioma.objects.get(codigo=request.POST.get('idioma'))  # codigo es la clave primaria
                    idioma_default = request.POST.get('idioma')
                except Exception:
                    pass
            
            # Procesar las variables con el idioma correspondiente
            zpl, variables_no_encontradas = procesar_variables_con_idioma(zpl, idioma_default)
            
            # Registrar variables no encontradas para seguimiento
            if variables_no_encontradas:
                info_adicional = f"Tipo etiqueta: {tipo_etiqueta}, Idioma: {idioma_default}"
                print(f"[visualizar_etiqueta] Variables no encontradas: {variables_no_encontradas}")
                print(f"[visualizar_etiqueta] Info adicional: {info_adicional}")
            
            # Actualizar el ZPL con las variables reemplazadas
            etiqueta.contenido_zpl = zpl
            
            # Renderizar usando el método correspondiente
            labelary = Labelary()
            img = labelary.renderizar_etiqueta(etiqueta)
            
            return render(request, 'etiquetas/png.html', {
                'imagen': img, 
                'variables': variables_encontradas,
                'idiomas': idiomas,
                'idioma_actual': idioma_default  # Para marcar el idioma seleccionado
            })
        
        except Exception as e:
            # Determinar el idioma actual (usar el valor por defecto si no se especificó)
            idioma_default = 'ES'
            if 'idioma' in request.POST and request.POST.get('idioma'):
                try:
                    # Verificar si el idioma solicitado existe en la base de datos
                    Idioma.objects.get(codigo=request.POST.get('idioma'))
                    idioma_default = request.POST.get('idioma')
                except Exception:
                    pass
                    
            return render(request, 'etiquetas/png.html', {
                'error': f'Error al visualizar: {str(e)}',
                'idiomas': idiomas,
                'idioma_actual': idioma_default
            })
    
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