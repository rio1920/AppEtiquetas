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
        """Limpia una variable ZPL, eliminando espacios y tomando solo antes de ';'"""
        return var.strip().split(';')[0]

    @staticmethod
    def agregar_var(var: str, variables: list):
        """Agrega una variable a la lista si no está y está limpia"""
        var_limpia = Patrones.limpiar_variable(var)
        if var_limpia and var_limpia not in variables:
            variables.append(var_limpia)

    @staticmethod
    def extraer_variables(zpl: str) -> list:
        """Extrae variables de un string ZPL usando expresiones regulares"""
        variables = []

        # Buscar patrón anidado [@var1[@var2@]@]
        patron_anidado = re.compile(r'\[@([^\[@]+)\[@([^@]+)@]@]')
        for externo, interno in patron_anidado.findall(zpl):
            Patrones.agregar_var(externo, variables)
            Patrones.agregar_var(interno, variables)

        # Buscar patrón simple [@Variable@]
        patron_simple = re.compile(r'\[@([^@]+)@]')
        for var in patron_simple.findall(zpl):
            Patrones.agregar_var(var, variables)

        return variables
    
    @staticmethod
    def extraer_variables_de_texto(texto: str) -> list:
        """Devuelve las variables completas tal como aparecen en el texto ZPL."""
        variables = set()

        # Anidados primero (más largos), ej: [@Externo[@Interno@]@]
        patron_anidado = re.compile(r'\[@[^\[@]+?\[@[^@]+?@]@]')
        variables.update(patron_anidado.findall(texto))

        # Luego simples, ej: [@Variable@]
        patron_simple = re.compile(r'\[@[^@]+?@]')
        variables.update(patron_simple.findall(texto))

        return list(variables)
    
    @staticmethod
    def extraer_var_limpia(variable_completa: str) -> str | None:
        
        patron = re.compile(r'\[@\s*([^\[@;]+)')
        match = patron.match(variable_completa)
        if match:
            return match.group(1).strip()
        return None