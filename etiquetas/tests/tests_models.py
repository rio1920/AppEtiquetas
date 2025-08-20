import pytest
from etiquetas.models import Impresora

@pytest.mark.django_db
def test_tipo_impresoras():
    impresora = Impresora.objects.create(dpi=300, descripcion="Impresora de etiquetas")
    assert str(impresora) == "(300 DPIS)"