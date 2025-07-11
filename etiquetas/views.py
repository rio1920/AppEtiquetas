from django.shortcuts import render, get_object_or_404
from .utils import Labelary, Patrones
from .models import Etiqueta, Variable

def etiqueta_png(request):
    if request.method == "POST":
        # Obtener el ZPL directamente o a través del ID de etiqueta
        if 'etiqueta_id' in request.POST:
            # Obtener la etiqueta por ID
            etiqueta_id = request.POST.get('etiqueta_id')
            etiqueta = get_object_or_404(Etiqueta, id=etiqueta_id)
            zpl = etiqueta.contenido_zpl
        else:
            # Modo antiguo - obtener ZPL directamente
            zpl = request.POST.get("etiqueta", "")
            etiqueta = None
            
        # Procesar variables en el ZPL
        variables_encontradas = Patrones.extraer_variables(zpl)
        variables_en_base_datos = Variable.objects.filter(codigo__in=variables_encontradas).values('codigo', 'default')
        diccionario_variables = {var['codigo']: var['default'] for var in variables_en_base_datos}
        extrer_variables_idem_texto = Patrones.extraer_variables_de_texto(zpl)
        
        # Reemplazar variables con sus valores predeterminados
        for var in variables_encontradas:
            if var not in diccionario_variables:
                print(f"Variable no definida: {var}", flush=True)
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
    
def index(request):
    variables = Variable.objects.values_list('codigo', flat=True)
    
    # Obtener etiquetas y agruparlas por tipo
    todas_etiquetas = Etiqueta.objects.all()
    rotulos_internos = Etiqueta.objects.filter(tipo_etiqueta='Rotulo Interno')
    etiquetas_externas = Etiqueta.objects.filter(tipo_etiqueta='Etiqueta Externa')
    
    # Obtener tipos únicos de etiquetas para el select
    tipos_etiquetas = Etiqueta.objects.values_list('tipo_etiqueta', flat=True).distinct()
    
    # Obtener una etiqueta para mostrar en el textarea
    try:
        etiqueta_ejemplo = Etiqueta.objects.first()
        descripcion_zpl = etiqueta_ejemplo.contenido_zpl if etiqueta_ejemplo else ""
    except Exception:
        descripcion_zpl = ""
    
    return render(request, 'etiquetas/index.html', {
        'descripcion_zpl': descripcion_zpl,
        'variables': variables,
        'etiquetas': None,
        'rotulos_internos': rotulos_internos,
        'etiquetas_externas': etiquetas_externas,
        'tipos_etiquetas': None
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
# 