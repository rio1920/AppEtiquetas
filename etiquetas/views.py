from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .utils import Labelary, Patrones, formatear_fecha
from .models import Etiqueta, Variable
from .models import Impresora, Insumo, Rotacion, Idioma
import re
import pdb
import json
from datetime import datetime

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

# def verificar_variable_definiciones(nombre_variable='Definiciones.sDescripcion'):
#     """
#     Función de diagnóstico para verificar si la variable específica existe en la base de datos
#     y qué idiomas tiene disponibles.
#     """
#     print(f"===== VERIFICACIÓN DE VARIABLE: {nombre_variable} =====")
#     try:
#         # Obtener todos los idiomas disponibles
#         idiomas = Idioma.objects.all().values_list('codigo', flat=True)
#         print(f"Idiomas disponibles en la base de datos: {list(idiomas)}")
        
#         # Buscar la variable en cada idioma
#         for idioma in idiomas:
#             try:
#                 variable_obj = Variable.objects.get(codigo=nombre_variable, idioma=idioma)
#                 print(f"✓ Variable '{nombre_variable}' encontrada en idioma '{idioma}': '{variable_obj.default}'")
#             except Variable.DoesNotExist:
#                 print(f"✗ Variable '{nombre_variable}' NO existe en idioma '{idioma}'")
#     except Exception as e:
#         print(f"Error al verificar variable: {str(e)}")
#     print("="*60)

def procesar_variables_con_idioma(zpl, idioma_default='ES'):
    """
    Procesa el ZPL para encontrar variables con idioma y reemplazarlas con los valores correspondientes.
    
    Args:
        zpl: String con el código ZPL
        idioma_default: Código del idioma por defecto si no se especifica uno (en mayúsculas)
    
    Returns:
        ZPL procesado, diccionario de variables no encontradas, y lista de variables que usan idioma por defecto
    """
    print(f"***** PROCESANDO ZPL CON IDIOMA: {idioma_default} *****")
    
    # # Verificar si la variable Definiciones.sDescripcion existe en la base de datos (diagnóstico)
    # verificar_variable_definiciones()
    # Extraer todas las variables del ZPL
    variables_encontradas = Patrones.extraer_variables(zpl)
    
    # Extraer variables con su idioma específico
    variables_con_idioma = Patrones.extraer_variables_con_idioma(zpl)
    
    # Lista para almacenar las variables que usan el idioma por defecto 'ES'
    variables_con_fallback_es = []
    
    # Guardar el idioma del template antes de procesar cualquier otra lógica de idioma
    # Este valor se usará SIEMPRE para los patrones FIIDIOMAVARIABLE
    idioma_template = idioma_default
    
    # PRIORIDAD 1: Procesar cualquier patrón que contenga FIIDIOMAVARIABLE usando el idioma del template
    # Esto debe hacerse antes de cualquier modificación de idioma_default
    patron_fiidiomavariable_general = re.compile(r'\[@([^@\[\];]+);\s*FIIDIOMAVARIABLE\s*@]', re.IGNORECASE)
    matches_fiidioma = patron_fiidiomavariable_general.findall(zpl)
    
    if matches_fiidioma:
        print(f"Encontrados {len(matches_fiidioma)} patrones con FIIDIOMAVARIABLE. Idioma del template: {idioma_template}")
    
    for match in matches_fiidioma:
        var_nombre = match.strip()
        var_limpia = Patrones.limpiar_variable(var_nombre)
        
        # SIEMPRE usamos el idioma seleccionado en el template para FIIDIOMAVARIABLE
        # Esto tiene prioridad sobre cualquier otra fuente de idioma
        idioma_var = idioma_template.upper() if idioma_template else 'ES'

        print(f"Procesando variable FIIDIOMAVARIABLE: {var_limpia} en idioma {idioma_var} (seleccionado en template)")

        try:
            # Buscar en el idioma seleccionado en el template
            variable_obj = Variable.objects.get(codigo=var_limpia, idioma=idioma_var)
            valor = variable_obj.default
            patron_completo = re.compile(rf'\[@{re.escape(var_nombre)};\s*FIIDIOMAVARIABLE\s*@]', re.IGNORECASE)
            
            # Log antes del reemplazo
            fragmento = zpl[max(0, zpl.find(f"[@{var_nombre};FIIDIOMAVARIABLE@]")-20):min(len(zpl), zpl.find(f"[@{var_nombre};FIIDIOMAVARIABLE@]")+40)]
            print(f"Reemplazando en ZPL: '{fragmento}' - Valor: '{valor}'")
            
            zpl = patron_completo.sub(valor, zpl)
            print(f"Variable '{var_limpia}' en idioma '{idioma_var}' reemplazada por '{valor}'")
        except Variable.DoesNotExist:
            try:
                # Si no existe con ese idioma, intentar con el idioma por defecto ES
                variable_obj = Variable.objects.get(codigo=var_limpia, idioma='ES')
                valor = variable_obj.default
                patron_completo = re.compile(rf'\[@{re.escape(var_nombre)};\s*FIIDIOMAVARIABLE\s*@]', re.IGNORECASE)
                
                # Log antes del reemplazo
                fragmento = zpl[max(0, zpl.find(f"[@{var_nombre};FIIDIOMAVARIABLE@]")-20):min(len(zpl), zpl.find(f"[@{var_nombre};FIIDIOMAVARIABLE@]")+40)]
                print(f"Reemplazando en ZPL (fallback ES): '{fragmento}' - Valor: '{valor}'")
                
                zpl = patron_completo.sub(valor, zpl)
                print(f"Variable '{var_limpia}' no encontrada en idioma '{idioma_var}', usando idioma por defecto ES: '{valor}'")
                
                # Agregar a la lista de variables con fallback a ES cuando el idioma solicitado no es ES
                if idioma_var != 'ES':
                    variables_con_fallback_es.append(var_limpia)
            except Variable.DoesNotExist:
                print(f"Variable '{var_limpia}' no encontrada en ningún idioma")
                patron_completo = re.compile(rf'\[@{re.escape(var_nombre)};\s*FIIDIOMAVARIABLE\s*@]', re.IGNORECASE)
                zpl = patron_completo.sub(var_limpia, zpl)
    
    # Para patrones que NO son FIIDIOMAVARIABLE, buscar si existe una variable IDIOMAVARIABLE en el ZPL
    # que sobrescriba el idioma_default
    idioma_from_zpl = None
    
    # Primero, verificar si hay un valor literal para IDIOMAVARIABLE en el formato [@IDIOMAVARIABLE=EN@]
    patron_idioma_valor = re.compile(r'\[@IDIOMAVARIABLE=(.*?)@]')
    matches = patron_idioma_valor.findall(zpl)
    if matches:
        idioma_from_zpl = matches[0].strip()
        print(f"Usando idioma literal desde ZPL: {idioma_from_zpl}")
        idioma_default = idioma_from_zpl.upper()
        
        # Reemplazar el patrón [@IDIOMAVARIABLE=valor@] por una cadena vacía
        zpl = re.sub(r'\[@IDIOMAVARIABLE=.*?@]', '', zpl)
    
    # Si no hay un valor literal, buscar si existe [@IDIOMAVARIABLE@] y obtener su valor de la BD
    elif 'IDIOMAVARIABLE' in variables_encontradas:
        patron_idioma_variable = re.compile(r'\[@IDIOMAVARIABLE@]')
        matches = patron_idioma_variable.findall(zpl)
        if matches:
            # El patrón [@IDIOMAVARIABLE@] está presente, necesitamos obtener su valor de la base de datos
            try:
                variable_obj = Variable.objects.get(codigo='IDIOMAVARIABLE')
                idioma_from_zpl = variable_obj.default
                print(f"Usando idioma desde variable en BD: {idioma_from_zpl}")
                if idioma_from_zpl:
                    idioma_default = idioma_from_zpl.upper()  # Actualizar el idioma por defecto
                    # Reemplazar [@IDIOMAVARIABLE@] con una cadena vacía después de procesarlo
                    zpl = zpl.replace('[@IDIOMAVARIABLE@]', '')
                    print(f"NOTA: El patrón FIIDIOMAVARIABLE seguirá usando el idioma del template: {idioma_template}")
            except Variable.DoesNotExist:
                print("Variable IDIOMAVARIABLE no encontrada en la base de datos")
    
    # Para cada variable, buscar su valor según el idioma correspondiente
    variables_procesadas = {}
    variables_no_encontradas = {}
    
    for var in variables_encontradas:
        # Determinar el idioma para esta variable
        idioma_asignado = variables_con_idioma.get(var, idioma_default)

        if idioma_asignado == "MULTI_IDIOMA":
            # Si el usuario seleccionó un idioma en el template, usar ese idioma
            idioma_seleccionado = idioma_default
            try:
                variable_obj = Variable.objects.get(codigo=var, idioma=idioma_seleccionado)
                variables_procesadas[var] = variable_obj.default
            except Variable.DoesNotExist:
                try:
                    # Si no existe con ese idioma, intentar con el idioma por defecto ES
                    variable_obj = Variable.objects.get(codigo=var, idioma='ES')
                    variables_procesadas[var] = variable_obj.default
                    print(f"Variable multi-idioma '{var}' no encontrada en idioma '{idioma_seleccionado}', usando idioma por defecto ES")
                    
                    # Agregar a la lista de variables con fallback a ES cuando el idioma seleccionado no es ES
                    if idioma_seleccionado != 'ES':
                        variables_con_fallback_es.append(var)
                except Variable.DoesNotExist:
                    variables_no_encontradas[var] = idioma_seleccionado
                    variables_procesadas[var] = None
                    print(f"Variable multi-idioma '{var}' no encontrada en ningún idioma")
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
                    
                    # Agregar a la lista de variables con fallback a ES cuando el idioma asignado no es ES
                    if idioma_asignado != 'ES' and idioma_default == 'ES':
                        variables_con_fallback_es.append(var)
                except Variable.DoesNotExist:
                    variables_no_encontradas[var] = idioma_asignado
                    variables_procesadas[var] = None
                    print(f"Variable '{var}' no encontrada en ningún idioma")
    
    # Log general para saber cómo se está reemplazando
    print(f"Variables encontradas: {variables_encontradas}")
    print(f"Variables procesadas: {list(variables_procesadas.keys())}")
    
    # Reemplazar las variables en el ZPL
    # Primero, procesar el patrón especial [@Variable[@IDIOMAVARIABLE@]@]
    patron_idioma_anidado = re.compile(r'\[@([^@\[\]]+)\[@IDIOMAVARIABLE@]@]')
    for match in patron_idioma_anidado.findall(zpl):
        var_limpia = Patrones.limpiar_variable(match)
        if var_limpia in variables_procesadas and variables_procesadas[var_limpia]:
            patron_completo = f"[@{match}[@IDIOMAVARIABLE@]@]"
            zpl = zpl.replace(patron_completo, variables_procesadas[var_limpia])
    
    # Procesar variables con formato especial [@Variable;;FI IDIOMA@]
    # Este patrón detecta algo como [@producto;;FI ITA@] donde "producto" es la variable e "ITA" es el idioma
    patron_idioma_fi = re.compile(r'\[@([^@\[\];]+);;FI\s+([^@\[\];]+)@]')
    for match in patron_idioma_fi.findall(zpl):
        var_nombre = match[0].strip()  # Nombre de la variable (ej: producto)
        idioma_var = match[1].strip().upper()  # Código del idioma (ej: ITA, EN, ES)
        var_limpia = Patrones.limpiar_variable(var_nombre)
        
        print(f"Procesando variable con idioma específico: {var_limpia} en {idioma_var}")
        
        try:
            # Buscar la variable con el idioma específico
            variable_obj = Variable.objects.get(codigo=var_limpia, idioma=idioma_var)
            valor = variable_obj.default
            # Reemplazar en el ZPL
            patron_completo = f"[@{var_nombre};;FI {match[1].strip()}@]"
            zpl = zpl.replace(patron_completo, valor)
            print(f"Variable '{var_limpia}' en idioma '{idioma_var}' reemplazada por '{valor}'")
        except Variable.DoesNotExist:
            try:
                # Si no existe con ese idioma, intentar con el idioma por defecto
                variable_obj = Variable.objects.get(codigo=var_limpia, idioma=idioma_default)
                valor = variable_obj.default
                # Reemplazar en el ZPL
                patron_completo = f"[@{var_nombre};;FI {match[1].strip()}@]"
                zpl = zpl.replace(patron_completo, valor)
                print(f"Variable '{var_limpia}' no encontrada en idioma '{idioma_var}', usando idioma por defecto: '{valor}'")
            except Variable.DoesNotExist:
                print(f"Variable '{var_limpia}' no encontrada en ningún idioma")
                # Si no se encuentra, mantener el texto original sin el formato
                patron_completo = f"[@{var_nombre};;FI {match[1].strip()}@]"
                zpl = zpl.replace(patron_completo, var_limpia)
        var_nombre = match.strip()
        var_limpia = Patrones.limpiar_variable(var_nombre)
        
        # SIEMPRE usamos el idioma seleccionado en el template para FIIDIOMAVARIABLE
        # Esto tiene prioridad sobre cualquier otra fuente de idioma
        idioma_var = idioma_template.upper() if idioma_template else 'ES'

        print(f"Procesando variable FIIDIOMAVARIABLE: {var_limpia} en idioma {idioma_var} (seleccionado en template)")

        try:
            # Buscar en el idioma seleccionado en el template
            variable_obj = Variable.objects.get(codigo=var_limpia, idioma=idioma_var)
            valor = variable_obj.default
            patron_completo = re.compile(rf'\[@{re.escape(var_nombre)};\s*FIIDIOMAVARIABLE\s*@]', re.IGNORECASE)
            
            # Log antes del reemplazo
            fragmento = zpl[max(0, zpl.find(f"[@{var_nombre};FIIDIOMAVARIABLE@]")-20):min(len(zpl), zpl.find(f"[@{var_nombre};FIIDIOMAVARIABLE@]")+40)]
            print(f"Reemplazando en ZPL: '{fragmento}' - Valor: '{valor}'")
            
            zpl = patron_completo.sub(valor, zpl)
            print(f"Variable '{var_limpia}' en idioma '{idioma_var}' reemplazada por '{valor}'")
        except Variable.DoesNotExist:
            try:
                # Si no existe con ese idioma, intentar con el idioma por defecto ES
                variable_obj = Variable.objects.get(codigo=var_limpia, idioma='ES')
                valor = variable_obj.default
                patron_completo = re.compile(rf'\[@{re.escape(var_nombre)};\s*FIIDIOMAVARIABLE\s*@]', re.IGNORECASE)
                
                # Log antes del reemplazo
                fragmento = zpl[max(0, zpl.find(f"[@{var_nombre};FIIDIOMAVARIABLE@]")-20):min(len(zpl), zpl.find(f"[@{var_nombre};FIIDIOMAVARIABLE@]")+40)]
                print(f"Reemplazando en ZPL (fallback ES): '{fragmento}' - Valor: '{valor}'")
                
                zpl = patron_completo.sub(valor, zpl)
                print(f"Variable '{var_limpia}' no encontrada en idioma '{idioma_var}', usando idioma por defecto ES: '{valor}'")
                
                # Agregar a la lista de variables con fallback a ES
                variables_con_fallback_es.append(var_limpia)
            except Variable.DoesNotExist:
                print(f"Variable '{var_limpia}' no encontrada en ningún idioma")
                patron_completo = re.compile(rf'\[@{re.escape(var_nombre)};\s*FIIDIOMAVARIABLE\s*@]', re.IGNORECASE)
                zpl = patron_completo.sub(var_limpia, zpl)
    
    # Procesar variables con idioma directo [@Variable;IDIOMA@] donde IDIOMA es un código como EN, ES, ITA, etc.
    patron_idioma_directo = re.compile(r'\[@([^@\[\];]+);([A-Za-z]{2,3})@]')
    for match in patron_idioma_directo.findall(zpl):
        var_nombre = match[0].strip()  # Nombre de la variable (ej: DefinicionesCuartos.sDescripcion)
        idioma_var = match[1].strip().upper()  # Código del idioma (ej: EN, ES, ITA)
        var_limpia = Patrones.limpiar_variable(var_nombre)
        
        print(f"Procesando variable con idioma directo: {var_limpia} en {idioma_var}")
        
        try:
            # Buscar la variable con el idioma específico
            variable_obj = Variable.objects.get(codigo=var_limpia, idioma=idioma_var)
            valor = variable_obj.default
            # Reemplazar en el ZPL
            patron_completo = f"[@{var_nombre};{match[1].strip()}@]"
            zpl = zpl.replace(patron_completo, valor)
            print(f"Variable '{var_limpia}' en idioma '{idioma_var}' reemplazada por '{valor}'")
        except Variable.DoesNotExist:
            try:
                # Si no existe con ese idioma, intentar con el idioma por defecto ES
                variable_obj = Variable.objects.get(codigo=var_limpia, idioma='ES')
                valor = variable_obj.default
                # Reemplazar en el ZPL
                patron_completo = f"[@{var_nombre};{match[1].strip()}@]"
                zpl = zpl.replace(patron_completo, valor)
                print(f"Variable '{var_limpia}' no encontrada en idioma '{idioma_var}', usando idioma por defecto ES: '{valor}'")
                
                # Agregar a la lista de variables con fallback a ES
                variables_con_fallback_es.append(var_limpia)
            except Variable.DoesNotExist:
                print(f"Variable '{var_limpia}' no encontrada en ningún idioma")
                # Si no se encuentra, mantener el texto original sin el formato
                patron_completo = f"[@{var_nombre};{match[1].strip()}@]"
                zpl = zpl.replace(patron_completo, var_limpia)
    
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
    
    # Eliminar duplicados de la lista de variables con fallback a ES
    if variables_con_fallback_es:
        variables_con_fallback_es = list(set(variables_con_fallback_es))
        print(f"Variables que utilizan el idioma por defecto (ES): {variables_con_fallback_es}")
        print(f"Total de variables con fallback a ES: {len(variables_con_fallback_es)}")
        print(f"Tipo de datos de variables_con_fallback_es: {type(variables_con_fallback_es)}")
        
        # Verificación adicional para cada variable en fallback
        for var in variables_con_fallback_es:
            try:
                # Verificar que existe en español pero no en el idioma solicitado
                variable_es = Variable.objects.get(codigo=var, idioma='ES')
                print(f"[visualizar_etiqueta] Variable '{var}' en idioma 'ES' tiene valor: '{variable_es.default}'")
                
                try:
                    Variable.objects.get(codigo=var, idioma=idioma_default)
                    print(f"[visualizar_etiqueta] Variable '{var}' SÍ existe en idioma '{idioma_default}'")
                except Variable.DoesNotExist:
                    print(f"[visualizar_etiqueta] Variable '{var}' NO existe en idioma '{idioma_default}'")
            except Variable.DoesNotExist:
                print(f"[visualizar_etiqueta] ATENCIÓN: La variable '{var}' no existe ni siquiera en ES!")
    else:
        print("No se encontraron variables con fallback a ES")
    
    # Ya no forzamos variables de prueba, dejamos que el sistema funcione normalmente
    
    return zpl, variables_no_encontradas, variables_con_fallback_es

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
            
            # Extraer todas las variables para mantener compatibilidad con el código existente
            variables_encontradas = Patrones.extraer_variables(zpl)
            
            # La lógica para extraer IDIOMAVARIABLE de diferentes formas ahora está en procesar_variables_con_idioma
            # Aquí sólo necesitamos asignar el idioma seleccionado en la UI si está disponible
            idioma_default = 'ES'  # Valor predeterminado
            
            # Si hay un idioma especificado en la solicitud, usarlo como valor inicial
            # Este será sobrescrito si hay un valor de idioma en el ZPL
            if 'idioma' in request.POST and request.POST.get('idioma'):
                idioma_solicitado = request.POST.get('idioma')
                try:
                    # Verificar si el idioma solicitado existe en la base de datos
                    from .models import Idioma
                    Idioma.objects.get(codigo=idioma_solicitado)  # codigo es la clave primaria
                    idioma_default = idioma_solicitado
                except Exception:
                    pass  # Si el idioma no existe, se mantiene el idioma por defecto
            
            # Debug del idioma seleccionado
            print(f"[etiqueta_png] Idioma seleccionado para procesar ZPL: {idioma_default}")
            print(f"[etiqueta_png] Ejemplo ZPL recibido (primeros 100 chars): {zpl[:100]}")
            
            # Procesar las variables con el idioma correspondiente
            zpl, variables_no_encontradas, variables_con_fallback_es = procesar_variables_con_idioma(zpl, idioma_default)
            
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
                
            # Convertir la lista de variables con fallback a JSON
            variables_fallback_json = json.dumps(variables_con_fallback_es) if variables_con_fallback_es else '[]'
            
            # Registrar en el log las variables con fallback para debug
            print(f"[visualizar_etiqueta] JSON de variables con fallback: {variables_fallback_json}")
            print(f"[visualizar_etiqueta] Contexto enviado - idioma_actual: {idioma_default}")
            print(f"[visualizar_etiqueta] Contexto enviado - variables_con_fallback_es: {variables_fallback_json}")
            
            # Si hay variables con fallback, garantizar que no se pierdan en la conversión
            variables_fallback_texto = ", ".join(variables_con_fallback_es) if variables_con_fallback_es else ""
            
            if img:
                return render(request, 'etiquetas/png.html', {
                    'imagen': img, 
                    'variables': variables_encontradas,
                    'idiomas': idiomas,
                    'idioma_actual': idioma_default,  # Para marcar el idioma seleccionado
                    'variables_con_fallback_es': variables_fallback_json,  # Variables que usan el idioma por defecto (como JSON)
                    'variables_fallback_texto': variables_fallback_texto,  # Variables como texto plano para respaldo
                    'tiene_fallbacks': len(variables_con_fallback_es) > 0,  # Flag booleano para simplicidad
                })
            else:
                return render(request, 'etiquetas/png.html', {
                    'error': 'No se pudo generar la imagen',
                    'idiomas': idiomas,
                    'idioma_actual': idioma_default,  # Mantener el idioma seleccionado incluso en caso de error
                    'variables_con_fallback_es': variables_fallback_json  # Variables que usan el idioma por defecto (como JSON)
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


# -- Visto

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
    pdb.set_trace()
    """Vista para renderizar una etiqueta específica por su ID"""
    # Obtener todos los idiomas para el selector
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
            Idioma.objects.get(codigo=request.GET.get('idioma'))  # codigo es la clave primaria
            idioma_default = request.GET.get('idioma')
        except Exception:
            pass
    
    # El valor de IDIOMAVARIABLE en el ZPL, si existe, tendrá prioridad sobre el idioma_default
    # Esto se maneja dentro de procesar_variables_con_idioma
    # Procesar las variables con el idioma correspondiente
    zpl, variables_no_encontradas, variables_con_fallback_es = procesar_variables_con_idioma(zpl, idioma_default)
    
    # Registrar variables no encontradas para seguimiento
    if variables_no_encontradas:
        info_adicional = f"Etiqueta ID: {etiqueta_id}, Nombre: '{etiqueta.nombre}', Idioma: {idioma_default}"
        print(f"[renderizar_etiqueta] Variables no encontradas: {variables_no_encontradas}")
        print(f"[renderizar_etiqueta] Info adicional: {info_adicional}")
        
    # Registrar variables que usan el idioma por defecto (ES)
    if variables_con_fallback_es:
        print(f"[renderizar_etiqueta] Variables usando idioma por defecto (ES): {variables_con_fallback_es}")
    
    # Actualizar el ZPL con variables reemplazadas
    etiqueta.contenido_zpl = zpl
    
    # Renderizar usando el nuevo método
    labelary = Labelary()
    img = labelary.renderizar_etiqueta(etiqueta)
    
    # Convertir la lista de variables con fallback a JSON
    variables_fallback_json = json.dumps(variables_con_fallback_es) if variables_con_fallback_es else '[]'
    print(f"[renderizar_etiqueta] Variables con fallback (JSON): {variables_fallback_json}")
    
    return render(request, 'etiquetas/png.html', {
        'imagen': img, 
        'variables': variables_encontradas,
        'idiomas': idiomas,
        'idioma_actual': idioma_default,  # Para marcar el idioma seleccionado
        'variables_con_fallback_es': variables_fallback_json  # Variables que usan el idioma por defecto (como JSON)
    })

# Vistas para manejar el ZPL de las etiquetas 
# --- VISTO

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
    
# --- VISTO

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
    
# --- Visto

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
            
            # Obtener los objetos relacionados si alguna falla lo caputa le bloque except y mostaramos el error
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


# VISTO
def visualizar_etiqueta(request):
    """Vista para visualizar una etiqueta con los parámetros seleccionados sin guardarla"""
    # Obtener todos los idiomas para el selector
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
                    Idioma.objects.get(codigo=request.POST.get('idioma'))  # codigo es la clave primaria
                    idioma_default = request.POST.get('idioma')
                except Exception:
                    pass
            
            # Debug del idioma seleccionado
            print(f"[visualizar_etiqueta] Idioma seleccionado para procesar ZPL: {idioma_default}")
            print(f"[visualizar_etiqueta] Ejemplo ZPL recibido (primeros 100 chars): {zpl[:100]}")
            print("[visualizar_etiqueta] Buscando patrones FIIDIOMAVARIABLE en ZPL...")
            
            # Buscar específicamente patrones FIIDIOMAVARIABLE antes de procesar
            patron_fiidioma = re.compile(r'\[@([^@\[\];]+);\s*FIIDIOMAVARIABLE\s*@]', re.IGNORECASE)
            matches = patron_fiidioma.findall(zpl)
            if matches:
                print(f"[visualizar_etiqueta] Encontrados {len(matches)} patrones FIIDIOMAVARIABLE: {matches}")
            
            # El valor de IDIOMAVARIABLE en el ZPL, si existe, tendrá prioridad sobre el idioma_default
            # Esto se maneja dentro de procesar_variables_con_idioma
            # Procesar las variables con el idioma correspondiente
            zpl, variables_no_encontradas, variables_con_fallback_es = procesar_variables_con_idioma(zpl, idioma_default)
            
            # Registrar variables no encontradas para seguimiento
            if variables_no_encontradas:
                info_adicional = f"Tipo etiqueta: {tipo_etiqueta}, Idioma: {idioma_default}"
                print(f"[visualizar_etiqueta] Variables no encontradas: {variables_no_encontradas}")
                print(f"[visualizar_etiqueta] Info adicional: {info_adicional}")
                
            # Registrar variables que usan el idioma por defecto (ES)
            if variables_con_fallback_es:
                print(f"[visualizar_etiqueta] Variables usando idioma por defecto (ES): {variables_con_fallback_es}")
            
            # Verificar si la variable Definiciones.sDescripcion existe en el idioma actual
            try:
                # Buscar específicamente los valores para diagnóstico
                for var_check in ["Definiciones.sDescripcion", "DefinicionesCuartos.sDescripcion"]:
                    try:
                        var_obj = Variable.objects.get(codigo=var_check, idioma=idioma_default)
                        print(f"[visualizar_etiqueta] Variable '{var_check}' en idioma '{idioma_default}' tiene valor: '{var_obj.default}'")
                    except Variable.DoesNotExist:
                        print(f"[visualizar_etiqueta] Variable '{var_check}' NO existe en idioma '{idioma_default}'")
            except Exception as e:
                print(f"[visualizar_etiqueta] Error al verificar variables: {str(e)}")
            
            # Actualizar el ZPL con las variables reemplazadas
            etiqueta.contenido_zpl = zpl
            
            # Renderizar usando el método correspondiente
            labelary = Labelary()
            img = labelary.renderizar_etiqueta(etiqueta)
            
            # Convertir la lista de variables con fallback a JSON
            variables_fallback_json = json.dumps(variables_con_fallback_es) if variables_con_fallback_es else '[]'
            print(f"[visualizar_etiqueta] JSON de variables con fallback: {variables_fallback_json}")
            
            # Para propósitos de prueba, si está en modo de prueba y no hay variables con fallback,
            # agregar algunas variables de prueba cuando el idioma no es español
            if idioma_default != 'ES' and request.GET.get('test_fallback') == '1':
                print("[visualizar_etiqueta] Modo de prueba - Agregando variables de prueba")
                variables_fallback_json = json.dumps(["Variable_Prueba1", "Variable_Prueba2"])
            
            # Crear el contexto para el template
            context = {
                'imagen': img, 
                'variables': variables_encontradas,
                'idiomas': idiomas,
                'idioma_actual': idioma_default,  # Para marcar el idioma seleccionado
                'variables_con_fallback_es': variables_fallback_json  # Variables que usan el idioma por defecto (como JSON)
            }
            
            print(f"[visualizar_etiqueta] Contexto enviado - idioma_actual: {context['idioma_actual']}")
            print(f"[visualizar_etiqueta] Contexto enviado - variables_con_fallback_es: {context['variables_con_fallback_es']}")
            
            return render(request, 'etiquetas/png.html', context)
        
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


#  ----- VISTO
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