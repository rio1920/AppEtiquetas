import pytest
from django.urls import reverse
from etiquetas.models import Variable, Etiqueta, Impresora, Insumo, Rotacion, Idioma

@pytest.mark.django_db
def test_index_view(client):
    # Crear datos de prueba en la DB temporal
    Insumo.objects.create(nombre="Insumo test")
    Idioma.objects.create(nombre="Español")
    impresora = Impresora.objects.create(dpi=300, descripcion="Impresora test")
    

    url = reverse("index")
    response = client.get(url)

    # Verificar que la vista responde 200
    assert response.status_code == 200

    # Verificar que se usa la plantilla correcta
    templates = [t.name for t in response.templates]
    assert 'etiquetas/index.html' in templates

    # Verificar que el contexto contiene los datos creados
    assert 'variables' in response.context
    assert 'descripcion_zpl' in response.context
    assert 'impresoras' in response.context
    assert response.context['impresoras'].count() == 1
