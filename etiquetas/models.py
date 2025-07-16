from django.db import models

# Create your models here.

class Impresora(models.Model):
    dpi = models.IntegerField()
    descripcion = models.CharField(max_length=50)
    
    def __str__(self):
        return f"({self.dpi} DPI)"

class Insumo(models.Model):
    nombre = models.CharField(max_length=50)
    tamanio = models.CharField(max_length=10)
    
    def __str__(self):
        return f"{self.tamanio}"

class Rotacion(models.Model):
    descripcion = models.CharField(max_length=50)
    angulo = models.IntegerField()
    
    def __str__(self):
        return f"{self.angulo}°"

class Etiqueta(models.Model):
    TIPO_CHOICES = [
        ('Rotulo Interno', 'Rotulo Interno'),
        ('Etiqueta Externa', 'Etiqueta Externa'),
    ]
    tipo_etiqueta = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=100)
    contenido_zpl = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    impresora = models.ForeignKey(Impresora, on_delete=models.CASCADE)
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    rotacion = models.ForeignKey(Rotacion, on_delete=models.CASCADE)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['tipo_etiqueta', 'nombre'], name='unique_nombre_por_tipo')
        ]
    
    def __str__(self):
        return self.nombre
    
class Idioma(models.Model):
    codigo = models.CharField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.codigo} ({self.nombre})"
    
# sustituyo las variables por el default  luego post a labelary para render de etiqueta
class Variable(models.Model):
    codigo = models.CharField(max_length=50) # Ejemplo: 'fechahoraimpresion'
    default = models.CharField(max_length=255) # Valor por defecto para la variable
    descripcion = models.CharField(max_length=255, blank=True, null=True) # Descripción opcional de la variable
    idioma = models.ForeignKey(Idioma, on_delete=models.CASCADE, default='ES', to_field='codigo') # Idioma por defecto es español (en mayúsculas)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['codigo', 'idioma'], name='unique_variable_por_idioma')
        ]

    def __str__(self):
        return f"{self.codigo} ({self.idioma.codigo})"
    
class TraduccionVariable(models.Model):
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name='traducciones')
    idioma = models.ForeignKey(Idioma, on_delete=models.CASCADE, to_field='codigo')
    descripcion = models.CharField(max_length=255)

    class Meta:
        unique_together = ('variable', 'idioma')
    
    def __str__(self):
        return f"{self.variable.codigo} ({self.idioma.codigo}): {self.descripcion}"
    
    
    # Primero en la tabla