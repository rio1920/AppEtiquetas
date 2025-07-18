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