# # '''  clases para intercatuar con el labelary nuestro '''
 

# # class Labelary():
# #     """ Clase para interactuar con el servicio de labelary """
 
# #     api = httpx.Client()
 
# #     def __init__(self, base_url="http://labelary.rioplatense.local/v1/printers/"):
# #         self.base_url = base_url
# #         self.rotulo_url   = self.base_url + '8dpmm/labels/4x5/0/'   # 203dpi
# #         self.primaria_url = self.base_url + '24dpmm/labels/4x5/0/'  # 600dpi
 
 
# #     def pngPrimaria(self, zpl:str):
# #         """ Baja un png de la etiqueta primaria """
 
# #         headers = {
# #             'X-Rotation':'270',
# #             # 'X-Linter':'On',
# #             'X-Quality':'grayscale'
# #             }
 
# #         response = self.api.post(self.primaria_url, data=zpl, headers=headers)
# #         if response.status_code != 200:
# #             raise ValueError(f"Error en la respuesta: {response.status_code} con payload: {zpl}")
        
# #         img = self.convertir_a_base64(response.content)
# #         return img
 
# #     def pngRotulo(self, zpl:str):
# #         """ Baja un png de la etiqueta de caja """
 
# #         headers = {
# #             'X-Rotation':'90',
# #             # 'X-Linter':'On',
# #             'X-Quality':'grayscale'
# #             }
 
# #         response = self.api.post(self.rotulo_url, data=zpl, headers=headers)
 
# #         if response.status_code != 200:
# #             raise ValueError(f"Error en la respuesta: {response.status_code} con payload: {zpl}")

# #         img = self.convertir_a_base64(response.content)
# #         return img
    
# #     def convertir_a_base64(self, imagen_bytes: bytes) -> str:
# #         """Convierte los bytes de la imagen a una cadena base64 con formato data URI."""
# #         imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
# #         data_uri = f"data:image/png;base64,{imagen_base64}"
# #         return data_uri
    
    

# # Reeemplazo de clase con metodo de clase y sin constructor

# import httpx
# import base64

# class Labelary:

#     api = httpx.Client()
#     base_url = "http://labelary.rioplatense.local/v1/printers/"
#     rotulo_url = base_url + '8dpmm/labels/4x5/0/'   # 203dpi
#     primaria_url = base_url + '24dpmm/labels/4x5/0/'  # 600dpi

#     @classmethod
#     def pngPrimaria(cls, zpl: str):
#         """ Baja un png de la etiqueta primaria """
#         headers = {
#             'X-Rotation': '270',
#             'X-Quality': 'grayscale'
#         }
#         response = cls.api.post(cls.primaria_url, data=zpl, headers=headers)
#         if response.status_code != 200:
#             raise ValueError(f"Error en la respuesta: {response.status_code} con payload: {zpl}")
#         return cls.convertir_a_base64(response.content)

#     @classmethod
#     def pngRotulo(cls, zpl: str):
#         """ Baja un png de la etiqueta de caja """
#         headers = {
#             'X-Rotation': '270', #90 
#             'X-Quality': 'grayscale'
#         }
#         response = cls.api.post(cls.rotulo_url, data=zpl, headers=headers)
#         if response.status_code != 200:
#             raise ValueError(f"Error en la respuesta: {response.status_code} con payload: {zpl}")
#         return cls.convertir_a_base64(response.content)

#     @staticmethod
#     def convertir_a_base64(imagen_bytes: bytes) -> str:
#         """Convierte los bytes de la imagen a una cadena base64 con formato data URI."""
#         imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
#         return f"data:image/png;base64,{imagen_base64}"


import httpx
import base64
import re

class Labelary:
    """Clase para interactuar con el servicio de Labelary"""
    
    api = httpx.Client()

    def __init__(self, base_url="http://labelary.rioplatense.local/v1/printers/"):
        self.base_url = base_url
    
    def generar_url_etiqueta(self, etiqueta):
        """Genera las URLs necesarias basadas en la configuración de la etiqueta"""
        impresora = etiqueta.impresora
        insumo = etiqueta.insumo
        
        # Construir URL con los valores de la impresora y el insumo
        dpi_str = f"{impresora.dpi}dpmm"
        # Ajustar formato del tamaño (ej: "4x6")
        tamanio = insumo.tamanio
        
        url = f"{self.base_url}{dpi_str}/labels/{tamanio}/0/"
               
        return url
    
    def renderizar_etiqueta(self, etiqueta):
        """Renderiza una etiqueta basada en su tipo y configuración"""
        try:
            url = self.generar_url_etiqueta(etiqueta)
            zpl = etiqueta.contenido_zpl
            if not zpl or not zpl.strip():
                return None
                
            angulo = etiqueta.rotacion.angulo
            

            
            # Tipo de etiqueta determina cómo procesarla
            if etiqueta.tipo_etiqueta == 'interno':
                return self.renderizar_png(url, zpl, angulo)
            else:  # 'externo'
                return self.renderizar_png(url, zpl, angulo)
        except Exception:
            # Log eliminado para producción
            return None
    
    def renderizar_png(self, url, zpl, angulo):
        """Renderiza un PNG con la configuración específica"""
        headers = {
            'X-Rotation': str(angulo),
            'X-Quality': 'grayscale',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Máximo de reintento
        max_intentos = 3
        intentos = 0
        
        while intentos < max_intentos:
            try:

                response = self.api.post(
                    url, 
                    data=zpl, 
                    headers=headers,
                    timeout=10.0  # Tiempo de espera razonable
                )
                
                if response.status_code == 200:

                    return self.convertir_a_base64(response.content)
                else:

                    raise ValueError(f"Error en la respuesta: {response.status_code}")
                    
            except Exception:

                intentos += 1
                if intentos >= max_intentos:
                    raise
        
        return None
    
    # Mantener métodos anteriores por compatibilidad
    def pngPrimaria(self, zpl: str, url=None) -> str:
        """Baja un PNG de la etiqueta primaria (alta calidad)"""
        headers = {
            'X-Rotation': '270',
            'X-Quality': 'grayscale'
        }
        if not url:
            url = self.base_url + '24dpmm/labels/4x5/0/'  # URL por defecto
        response = self.api.post(url, data=zpl, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Error en la respuesta: {response.status_code} con payload: {zpl}")
        return self.convertir_a_base64(response.content)

    def pngRotulo(self, zpl: str, url=None) -> str:
        """Baja un PNG de la etiqueta de caja (rotación diferente)"""
        headers = {
            'X-Rotation': '90',  # diferente de la primaria
            'X-Quality': 'grayscale'
        }
        if not url:
            url = self.base_url + '8dpmm/labels/4x5/0/'     # URL por defecto
        response = self.api.post(url, data=zpl, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Error en la respuesta: {response.status_code} con payload: {zpl}")
        return self.convertir_a_base64(response.content)

    @staticmethod
    def convertir_a_base64(imagen_bytes: bytes) -> str:
        """Convierte los bytes de imagen a formato base64 como data URI"""
        imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
        return f"data:image/png;base64,{imagen_base64}"
    
    
def formatear_fecha(fecha_str, formato_zpl, formato_entrada=None):
    """
    Formatea una fecha según el formato especificado en el ZPL.
    
    Args:
        fecha_str: String con la fecha en cualquier formato reconocible o un objeto datetime
        formato_zpl: String con el formato de fecha del ZPL (e.j., "FFdd/MM/yyyy")
        formato_entrada: Formato de entrada opcional si se conoce específicamente
        
    Returns:
        String con la fecha formateada según el formato especificado
    """
    from datetime import datetime
    import re
    import platform
    
    # Para debugging
    es_windows = platform.system() == 'Windows'
    print(f"Sistema operativo: {platform.system()}, es Windows: {es_windows}")
    print(f"Formato ZPL solicitado: {formato_zpl}")
    
    # Si el valor es None o vacío, devolver string vacío
    if not fecha_str:
        return ""
        
    # Si ya es un objeto datetime, usarlo directamente
    if isinstance(fecha_str, datetime):
        fecha = fecha_str
    # Si es un string, intentar convertirlo
    elif isinstance(fecha_str, str):
        fecha_str = fecha_str.strip()
        fecha = None
        
        # 1. Si se proporciona un formato de entrada, intentar usarlo primero
        if formato_entrada:
            try:
                # Convertir formato especificado a formato Python
                formato_python = formato_entrada
                formato_python = formato_python.replace('dd', '%d')
                formato_python = formato_python.replace('MM', '%m')
                formato_python = formato_python.replace('yyyy', '%Y')
                formato_python = formato_python.replace('yy', '%y')
                fecha = datetime.strptime(fecha_str, formato_python)
                print(f"Fecha parseada con formato especificado: {fecha}")
            except ValueError:
                print(f"No se pudo parsear la fecha '{fecha_str}' con formato '{formato_entrada}'")
        
        # 2. Si no hay formato de entrada o falló, intentar formatos comunes
        if not fecha:
            formatos_comunes = [
                # ISO format (yyyy-mm-dd)
                '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', 
                # Formatos con guiones
                '%d-%m-%Y', '%m-%d-%Y', '%Y-%d-%m',
                # Formatos con barras
                '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%Y/%d/%m',
                # Formatos con puntos
                '%d.%m.%Y', '%m.%d.%Y', '%Y.%m.%d', '%Y.%d.%m',
                # Formatos de año corto
                '%d-%m-%y', '%m-%d-%y', '%y-%m-%d', '%y-%d-%m',
                '%d/%m/%y', '%m/%d/%y', '%y/%m/%d', '%y/%d/%m',
                '%d.%m.%y', '%m.%d.%y', '%y.%m.%d', '%y.%d.%m',
            ]
            
            for fmt in formatos_comunes:
                try:
                    fecha = datetime.strptime(fecha_str, fmt)
                    print(f"Fecha '{fecha_str}' parseada con formato: {fmt}")
                    break
                except ValueError:
                    continue
                    
        # 3. Intentar con ISO format usando fromisoformat (más flexible)
        if not fecha:
            try:
                # Algunas fechas ISO pueden tener 'Z' o '+00:00' al final
                fecha_limpia = fecha_str.replace('Z', '+00:00')
                fecha = datetime.fromisoformat(fecha_limpia)
                print(f"Fecha parseada con fromisoformat: {fecha}")
            except ValueError:
                pass
                
        # 4. Intentar extraer componentes de fecha usando regex
        if not fecha:
            # Buscar patrones de fecha comunes (dd/mm/yyyy, yyyy-mm-dd, etc.)
            # Patrón para detectar fechas con separadores
            patron_fecha = re.compile(r'(\d{1,4})[-./](\d{1,2})[-./](\d{1,4})')
            match = patron_fecha.search(fecha_str)
            
            if match:
                # Extraer componentes
                comp1, comp2, comp3 = match.groups()
                
                # Determinar qué componente es qué (año, mes, día)
                if len(comp1) == 4:  # Si el primer componente tiene 4 dígitos, es probable que sea el año
                    year, month, day = comp1, comp2, comp3
                elif len(comp3) == 4:  # Si el último componente tiene 4 dígitos, es probable que sea el año
                    day, month, year = comp1, comp2, comp3
                else:  # En caso de duda, asumir formato dd/mm/yy o mm/dd/yy (dependiendo del valor del mes)
                    # Determinar mes vs día
                    if 1 <= int(comp1) <= 12 and int(comp2) > 12:  # Probable mm/dd/yy
                        month, day, year = comp1, comp2, comp3
                    else:  # Probable dd/mm/yy
                        day, month, year = comp1, comp2, comp3
                        
                # Convertir a enteros
                try:
                    year, month, day = int(year), int(month), int(day)
                    
                    # Ajustar año de 2 dígitos
                    if year < 100:
                        year = 2000 + year if year < 50 else 1900 + year
                        
                    # Verificar rangos válidos
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1000 <= year <= 9999:
                        try:
                            fecha = datetime(year, month, day)
                            print(f"Fecha parseada con regex: {fecha}")
                        except ValueError as e:
                            print(f"Error al crear fecha: {e}")
                except ValueError as e:
                    print(f"Error al convertir componentes de fecha: {e}")
        
        # Si no pudimos convertir, devolver el string original
        if not fecha:
            print(f"No se pudo parsear la fecha: '{fecha_str}'")
            return fecha_str
    else:
        # Si no es string ni datetime, devolver el valor convertido a string
        print(f"Tipo de fecha no soportado: {type(fecha_str)}")
        return str(fecha_str)
    
    # Procesar el formato de salida (ZPL)
    # FF - Puede estar como prefijo o en medio del formato (por ejemplo, FFdd o yyyy/MM/FFdd)
    formato_zpl = formato_zpl.strip()
    
    # Verificar si hay "FF" en cualquier parte del formato y quitarlo
    formato_zpl = formato_zpl.replace('FF', '')
    formato_zpl = formato_zpl.replace('ff', '')
    
    try:
        # Para Windows, necesitamos un enfoque diferente ya que %-d no funciona
        # En lugar de usar strftime, formateamos manualmente
        
        # Obtener los componentes de la fecha
        dia = fecha.day
        mes = fecha.month
        anio = fecha.year
        hora = fecha.hour
        minuto = fecha.minute
        segundo = fecha.second
        
        print(f"Fecha analizada: día={dia}, mes={mes}, año={anio}")
        
        # Verificar si el formato es solo "dd" después de quitar FF - caso especial
        print(f"Verificando formato especial: '{formato_zpl.upper()}'")
        if formato_zpl.upper().replace(' ', '') == 'DD' or formato_zpl.lower().replace(' ', '') == 'dd':
            # Si solo se pide el día, devolver solo el día sin importar el formato de entrada
            print(f"Formato especial solo día detectado: {formato_zpl}")
            return f"{dia:02d}"
            
        # Crear el formato de salida según el patrón ZPL
        formato_limpio = formato_zpl
            
        # Reemplazar directamente los componentes en el formato
        resultado = formato_limpio
        
        # Reemplazar patrones de año
        if 'yyyy' in resultado:
            resultado = resultado.replace('yyyy', f"{anio:04d}")
        elif 'yy' in resultado:
            resultado = resultado.replace('yy', f"{anio % 100:02d}")
            
        # Reemplazar patrones de mes
        if 'MM' in resultado:
            resultado = resultado.replace('MM', f"{mes:02d}")
        elif 'M' in resultado:
            resultado = resultado.replace('M', f"{mes}")
            
        # Reemplazar patrones de día
        if 'dd' in resultado:
            resultado = resultado.replace('dd', f"{dia:02d}")
        elif 'd' in resultado:
            resultado = resultado.replace('d', f"{dia}")
            
        # Reemplazar otros componentes si son necesarios
        if 'HH' in resultado:
            resultado = resultado.replace('HH', f"{hora:02d}")
        if 'mm' in resultado:
            resultado = resultado.replace('mm', f"{minuto:02d}")
        if 'ss' in resultado:
            resultado = resultado.replace('ss', f"{segundo:02d}")
        
        # Ya no necesitamos usar strftime, hemos reemplazado directamente todos los componentes
            
        print(f"Fecha formateada: '{fecha_str}' -> '{resultado}' (formato: {formato_zpl})")
        return resultado
    except Exception as e:
        print(f"Error al formatear fecha: {e}")
        return fecha_str

class Patrones:
    """Clase para manejar patrones de ZPL y extraer variables"""

    @staticmethod
    def limpiar_variable(var: str) -> str:
        """Limpia una variable ZPL, eliminando espacios, comillas y tomando solo antes de ';'"""
        # Primero eliminamos espacios
        var_limpia = var.strip()
        # Eliminamos comillas dobles si existen
        var_limpia = var_limpia.replace('"', '')
        # Tomamos solo la parte antes del punto y coma (parámetros adicionales)
        var_limpia = var_limpia.split(';')[0]
        return var_limpia

    @staticmethod
    def agregar_var(var: str, variables: list, idiomas=None):
        """
        Agrega una variable a la lista si no está y está limpia
        Si se proporciona el parámetro idiomas, también extrae el idioma de la variable
        """
        var_limpia = Patrones.limpiar_variable(var)
        if var_limpia and var_limpia not in variables:
            variables.append(var_limpia)
            
        # Si se especifica el parámetro idiomas, verificar si la variable tiene formato IDIOMAVARIABLE
        if idiomas is not None and 'IDIOMAVARIABLE' in var_limpia:
            # Añadir IDIOMAVARIABLE a la lista de idiomas
            idiomas.append('IDIOMAVARIABLE')

    @staticmethod
    def extraer_variables(zpl: str) -> list:
        """Extrae variables de un string ZPL usando expresiones regulares"""
        variables = []
        idiomas = []

        # Patrón para variables de fecha: [@Variable;FFdd/MM/yyyy@] y otros formatos
        patron_fecha = re.compile(r'\[@([^@\[\];]+);([FfDdMmYyHhSs/.-:]+)@]')
        for variable, formato in patron_fecha.findall(zpl):
            var_limpia = Patrones.limpiar_variable(variable)
            if var_limpia and var_limpia not in variables:
                variables.append(var_limpia)
            # No necesitamos hacer nada con el formato aquí, solo extraer la variable
                
        # Patrón para variables con asignación de valor: [@IDIOMAVARIABLE=valor@]
        patron_idioma_valor = re.compile(r'\[@IDIOMAVARIABLE=([^@\[\]]+)@]')
        for valor in patron_idioma_valor.findall(zpl):
            # Agregar IDIOMAVARIABLE a la lista de variables encontradas
            if 'IDIOMAVARIABLE' not in variables:
                variables.append('IDIOMAVARIABLE')

        # Patrón especificado: [@Variable[@IDIOMAVARIABLE@]@]
        # Primero extraemos este patrón específico
        patron_variable_idioma = re.compile(r'\[@([^@\[\]]+)\[@([^@\[\]]+)@]@]')
        for variable, idioma_var in patron_variable_idioma.findall(zpl):
            Patrones.agregar_var(variable, variables)
            # Si la variable interna es IDIOMAVARIABLE, la agregamos también
            if idioma_var == "IDIOMAVARIABLE":
                idiomas.append(idioma_var)
            else:
                Patrones.agregar_var(idioma_var, variables)

        # Buscar patrón con idioma tradicional [@Variable@IDIOMAVARIABLE@] 
        # incluyendo variables con comillas y parámetros [@"Variable";params@IDIOMAVARIABLE@]
        patron_con_idioma = re.compile(r'\[@([^@\[\];]+(?:;[^@\[\]]+)?)@([^@\[\]]+)@]')
        for var, idioma in patron_con_idioma.findall(zpl):
            # Evitamos capturar el patrón anterior nuevamente
            if not re.search(r'\[@[^@\[\]]+\[@[^@\[\]]+@]@]', f"[@{var}@{idioma}@]"):
                Patrones.agregar_var(var, variables)
                idiomas.append(idioma.strip())

        # Buscar patrón anidado general [@var1[@var2@]@] que no sea el específico de idiomas
        patron_anidado = re.compile(r'\[@([^@\[\];]+(?:;[^@\[\]]+)?)\[@([^@\[\];]+(?:;[^@\[\]]+)?)@]@]')
        for externo, interno in patron_anidado.findall(zpl):
            # Evitar duplicados ya capturados por patron_variable_idioma
            var_externo = Patrones.limpiar_variable(externo)
            var_interno = Patrones.limpiar_variable(interno)
            if interno != "IDIOMAVARIABLE" and not (var_externo in variables and var_interno in variables):
                Patrones.agregar_var(externo, variables)
                Patrones.agregar_var(interno, variables)

        # Buscar patrón simple [@Variable@] incluyendo variables con comillas y parámetros [@"Variable";params@]
        patron_simple = re.compile(r'\[@([^@\[\];]+(?:;[^@\[\]]+)?)@]')
        for var in patron_simple.findall(zpl):
            # Evitar duplicados que ya fueron capturados
            if '@' not in var and '[' not in var and ']' not in var:
                Patrones.agregar_var(var, variables)

        return variables
    
    @staticmethod
    def extraer_variables_con_idioma(zpl: str) -> dict:
        """
        Extrae variables y sus idiomas asociados del ZPL
        Retorna un diccionario con la variable como clave y el idioma como valor
        """
        variables_con_idioma = {}
        
        # Buscar patrón [@Variable[@IDIOMAVARIABLE@]@]
        patron_idioma_anidado = re.compile(r'\[@([^@\[\]]+)\[@IDIOMAVARIABLE@]@]')
        for var in patron_idioma_anidado.findall(zpl):
            var_limpia = Patrones.limpiar_variable(var)
            # Para este patrón específico, sabemos que queremos buscar la variable en todos los idiomas
            # disponibles, así que marcamos esto de manera especial
            variables_con_idioma[var_limpia] = "MULTI_IDIOMA"
        
        # Buscar patrón con idioma tradicional [@Variable@Idioma@]
        patron_con_idioma = re.compile(r'\[@([^@\[\]]+)@([^@\[\]]+)@]')
        for var, idioma in patron_con_idioma.findall(zpl):
            # Evitar capturar nuevamente los patrones de idioma anidado
            if not re.search(r'\[@[^@\[\]]+\[@IDIOMAVARIABLE@]@]', f"[@{var}@{idioma}@]"):
                var_limpia = Patrones.limpiar_variable(var)
                variables_con_idioma[var_limpia] = idioma.strip()
            
        return variables_con_idioma
    
    @staticmethod
    def extraer_variables_de_texto(texto: str) -> list:
        """Devuelve las variables completas tal como aparecen en el texto ZPL."""
        variables = set()

        # Variables de fecha, ej: [@Variable;FFdd/MM/yyyy@] y otros formatos
        patron_fecha = re.compile(r'\[@[^@\[\];]+;[FfDdMmYyHhSs/.-:]+@]')
        variables.update(patron_fecha.findall(texto))

        # Variables con idioma [@Variable@Idioma@]
        patron_con_idioma = re.compile(r'\[@[^@]+@[^@]+@]')
        variables.update(patron_con_idioma.findall(texto))

        # Anidados luego, ej: [@Externo[@Interno@]@]
        patron_anidado = re.compile(r'\[@[^\[@]+?\[@[^@]+?@]@]')
        variables.update(patron_anidado.findall(texto))

        # Luego simples, ej: [@Variable@]
        patron_simple = re.compile(r'\[@[^@]+?@]')
        for match in patron_simple.findall(texto):
            # Evitar duplicados que ya fueron capturados por patron_con_idioma
            if match.count('@') <= 2:
                variables.add(match)

        return list(variables)
    
    @staticmethod
    def extraer_formato_fecha(variable_completa: str) -> tuple:
        """
        Extrae el nombre de la variable y el formato de fecha si existe
        
        Args:
            variable_completa: La variable completa del ZPL
            
        Returns:
            tuple: (nombre_variable, formato_fecha) o (None, None) si no se encuentra
        """
        # Para formato de fecha [@Variable;FFdd/MM/yyyy@]
        patron_fecha = re.compile(r'\[@\s*([^@\[\];]+);([FfDdMmYyHhSs/.-:]+)@]')
        match = patron_fecha.search(variable_completa)
        if match:
            var = match.group(1).strip()
            formato = match.group(2).strip()
            return Patrones.limpiar_variable(var), formato
        
        return None, None
    
    @staticmethod
    def extraer_var_limpia(variable_completa: str) -> str | None:
        """Extrae el nombre de la variable de la expresión completa"""
        # Para formato [@Variable[@IDIOMAVARIABLE@]@]
        patron_idioma_anidado = re.compile(r'\[@([^@\[\]]+)\[@IDIOMAVARIABLE@]@]')
        match = patron_idioma_anidado.search(variable_completa)
        if match:
            var = match.group(1).strip()
            return Patrones.limpiar_variable(var)
            
        # Para formato [@Variable@] incluyendo casos con comillas y parámetros como [@"Variable";param@]
        patron = re.compile(r'\[@\s*([^@\[\];]+(?:;[^@\[\]]+)?)(@|@\])')
        match = patron.search(variable_completa)
        if match:
            var = match.group(1).strip()
            return Patrones.limpiar_variable(var)
        
        # Para formato [@Variable@Idioma@] incluyendo casos con comillas
        patron_con_idioma = re.compile(r'\[@\s*([^@\[\];]+(?:;[^@\[\]]+)?)@')
        match = patron_con_idioma.search(variable_completa)
        if match:
            var = match.group(1).strip()
            return Patrones.limpiar_variable(var)
            
        return None
        
    @staticmethod
    def extraer_idioma(variable_completa: str) -> str | None:
        """Extrae el idioma de una variable con formato [@Variable@Idioma@]"""
        patron = re.compile(r'\[@[^@]+@([^@]+)@]')
        match = patron.search(variable_completa)
        if match:
            return match.group(1).strip()
        return None
        
    @staticmethod
    def detectar_y_formatear_fechas_literales(zpl: str) -> str:
        """
        Detecta fechas literales en el texto ZPL y las formatea según patrones de formato
        especificados (si existen)
        
        Args:
            zpl: String con el texto ZPL
            
        Returns:
            String con el texto ZPL con las fechas literales formateadas
        """
        import re
        
        # Patrón para detectar fechas literales seguidas de formato, por ejemplo: 2025-12-31;FFdd/MM/yyyy
        # Este patrón busca una fecha (con varios formatos posibles) seguida de un punto y coma
        # y un formato de fecha (que empieza con FF o no)
        patron_fecha_con_formato = re.compile(
            r'(\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4}|\d{2}/\d{2}/\d{4}|\d{4}/\d{2}/\d{2}|\d{2}\.\d{2}\.\d{4}|\d{4}\.\d{2}\.\d{2});([FfDdMmYyHhSs/.-:]+)'
        )
        
        # Reemplazar todas las ocurrencias encontradas
        for match in patron_fecha_con_formato.finditer(zpl):
            fecha_literal = match.group(1)
            formato = match.group(2)
            
            # Intentar formatear la fecha
            try:
                fecha_formateada = formatear_fecha(fecha_literal, formato)
                # Reemplazar en el ZPL
                zpl = zpl.replace(f"{fecha_literal};{formato}", fecha_formateada)
                print(f"Fecha literal '{fecha_literal}' formateada según '{formato}' -> '{fecha_formateada}'")
            except Exception as e:
                print(f"Error al formatear fecha literal: {e}")
        
        # También buscar fechas literales sin formato específico
        # En este caso podríamos dejarlas como están o aplicar un formato predeterminado
        # Por ahora las dejamos como están
        
        return zpl