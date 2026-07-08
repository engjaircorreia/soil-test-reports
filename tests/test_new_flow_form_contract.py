import pytest
from django.urls import reverse

from ensaios.models import Job


@pytest.mark.django_db
def test_upload_form_marks_required_fields_with_asterisk(client):
    response = client.get(reverse("ensaios:upload"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Obra *" in content
    assert "Procedência / rua *" in content or "Procedencia / rua *" in content
    assert "Local / furo / estaca *" in content
    assert "Data do ensaio *" in content
    assert "Energia Proctor *" in content


@pytest.mark.django_db
def test_upload_form_hides_granulometry_company_when_proctor_cbr_is_selected(client):
    response = client.get(reverse("ensaios:upload"))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'data-visible-for="granulometria"' in content
    assert 'name="gran_empresa_executora"' in content
    assert 'data-visible-for="compactacao_cbr"' not in content.split('name="gran_empresa_executora"')[0][-300:]


@pytest.mark.django_db
def test_review_form_marks_calculated_fields_as_readonly(client):
    job = Job.objects.create(status=Job.STATUS_REVIEW_PENDING, language="pt", test_type="compactacao_cbr")
    response = client.get(reverse("ensaios:review", args=[job.id]))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'data-calculated-field="true"' in content
    assert "readonly" in content
