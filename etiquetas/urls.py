from django.urls import path
from .views import index, etiqueta_png, renderizar_etiqueta
urlpatterns = [
    path('', index, name='index'),
    path('png/', etiqueta_png, name='etiqueta_png'),
    path('renderizar/<int:etiqueta_id>/', renderizar_etiqueta, name='renderizar_etiqueta'),
]
