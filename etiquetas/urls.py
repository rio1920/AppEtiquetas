from django.urls import path
from .views import (
    index, etiqueta_png, renderizar_etiqueta, get_zpl, actualizar_zpl,
    crear_etiqueta, visualizar_etiqueta, actualizar_nombre_etiqueta, duplicar_etiqueta
)

urlpatterns = [
    path('', index, name='index'),
    path('png/', etiqueta_png, name='etiqueta_png'),
    path('renderizar/<int:etiqueta_id>/', renderizar_etiqueta, name='renderizar_etiqueta'),
    path('get_zpl/<int:etiqueta_id>/', get_zpl, name='get_zpl'),
    path('actualizar_zpl/', actualizar_zpl, name='actualizar_zpl'),
    path('crear_etiqueta/', crear_etiqueta, name='crear_etiqueta'),
    path('visualizar_etiqueta/', visualizar_etiqueta, name='visualizar_etiqueta'),
    path('actualizar_nombre_etiqueta/', actualizar_nombre_etiqueta, name='actualizar_nombre_etiqueta'),
    path('duplicar_etiqueta/', duplicar_etiqueta, name='duplicar_etiqueta'),
]
