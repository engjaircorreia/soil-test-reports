import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from ensaios.models import Job
from ensaios.views import empty_review_fields, form_to_reviewed_data, preserve_extracted_technical_details
from ensaios.forms import ReviewForm


@pytest.mark.django_db
def test_upload_page_loads(client):
    response = client.get(reverse("ensaios:upload"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "static/js/app.js" in content
    assert "Detectar automaticamente" in content
    assert 'name="data_ensaio"' not in content
    assert 'name="empresa_executora"' not in content
    assert 'data-test-block="proctor"' in content
    assert 'data-test-block="cbr"' in content
    assert 'data-test-block="granulometria"' in content
    assert 'name="gran_empresa_executora"' in content
    assert 'name="cbr_obra"' not in content
    assert 'name="cbr_registro"' in content
    assert 'name="cbr_numero_camadas"' in content
    assert 'name="cbr_golpes_camada"' in content
    assert 'name="cbr_peso_molde"' in content
    assert 'value="5436"' in content
    assert 'value="3210"' in content
    assert 'value="0,0839"' in content
    assert "data-selected-files" in content
    assert "calculista" not in content.lower()
    assert "visto" not in content.lower()


def test_reviewed_data_keeps_test_admin_blocks_separate():
    data = form_to_reviewed_data(
        {
            "test_type": "compactacao_cbr",
            "language": "pt",
            "proctor_obra": "Obra Proctor",
            "proctor_estaca": "Estaca 01",
            "proctor_interessado": "Cliente",
            "cbr_registro": "CBR-02",
            "cbr_numero_camadas": "5",
            "cbr_golpes_camada": "26",
            "gran_empresa_executora": "RCA",
            "gran_obra": "Obra Granulometria",
            "gran_estaca": "Estaca 03",
        }
    )
    assert data["proctor_admin"]["obra"] == "Obra Proctor"
    assert data["cbr_admin"]["registro"] == "CBR-02"
    assert data["cbr_admin"]["numero_camadas"] == "5"
    assert data["cbr_admin"]["golpes_camada"] == "26"
    assert data["granulometria_admin"]["empresa_executora"] == "RCA"
    assert data["empresa_executora"] == "RCA"
    assert data["obra"] == "Obra Proctor"


def test_reviewed_data_does_not_put_testing_company_in_proctor_or_cbr():
    data = form_to_reviewed_data(
        {
            "test_type": "ambos",
            "language": "pt",
            "proctor_obra": "Obra Proctor",
            "gran_empresa_executora": "Empresa só da granulometria",
        }
    )
    assert "empresa_executora" not in data["proctor_admin"]
    assert "empresa_executora" not in data["cbr_admin"]
    assert data["granulometria_admin"]["empresa_executora"] == "Empresa só da granulometria"


def test_reviewed_data_preserves_extracted_moisture_details():
    reviewed = form_to_reviewed_data(
        {
            "test_type": "compactacao_cbr",
            "language": "pt",
            "umidade_otima": "9.8",
            "densidade_maxima": "1.958",
            "cbr": "34",
            "expansao": "0.5",
        }
    )
    extracted = {
        "cbr": {
            "higroscopica": {"capsula": "31", "peso_bruto_umido": 101.7},
            "moldagem": {"capsula": "40", "peso_bruto_umido": 100.4},
            "peso_solo_umido_passando_peneira_4": 6.88,
            "calculo_moldagem": {"peso_solo_umido": 6000},
            "verificacao_moldagem": {"peso_bruto_cp_umido": 9620},
            "leituras": [{"tempo": "30 s"}],
        }
    }
    preserved = preserve_extracted_technical_details(reviewed, extracted)
    assert preserved["cbr"]["cbr"] == "34"
    assert preserved["cbr"]["higroscopica"]["capsula"] == "31"
    assert preserved["cbr"]["moldagem"]["capsula"] == "40"
    assert preserved["cbr"]["peso_solo_umido_passando_peneira_4"] == 6.88
    assert preserved["cbr"]["calculo_moldagem"]["peso_solo_umido"] == 6000
    assert preserved["cbr"]["verificacao_moldagem"]["peso_bruto_cp_umido"] == 9620


def test_empty_review_fields_reports_only_missing_visible_fields():
    form = ReviewForm(
        {
            "test_type": "compactacao_cbr",
            "language": "pt",
            "proctor_energia": "INTERMEDIÁRIO",
            "proctor_data_ensaio": "2026-07-08",
            "cbr_molde_numero": "02",
            "cbr_peso_molde": "5436",
            "cbr_volume_molde": "3210",
            "cbr_numero_camadas": "5",
            "cbr_golpes_camada": "26",
            "cbr_peso_soquete": "4536",
            "cbr_espessura_disco": '2½"',
            "cbr_altura_cilindro": "114",
            "cbr_constante_prensa": "0,0839",
        }
    )
    assert form.is_valid()
    missing = empty_review_fields(form, form.cleaned_data)
    assert "Obra" in missing
    assert "Observações" not in missing
    assert "Empresa executora" not in missing


def test_empty_review_fields_no_message_when_complete():
    form = ReviewForm(
        {
            "test_type": "compactacao_cbr",
            "language": "pt",
            "proctor_interessado": "Cliente",
            "proctor_obra": "Obra",
            "proctor_energia": "INTERMEDIÁRIO",
            "proctor_registro": "101",
            "proctor_estaca": "Estaca 01",
            "proctor_profundidade": "0,80m",
            "proctor_data_ensaio": "2026-07-08",
            "proctor_procedencia": "Rua",
            "proctor_cidade": "Cidade",
            "proctor_responsavel_tecnico": "Responsável",
            "cbr_registro": "102",
            "cbr_molde_numero": "02",
            "cbr_peso_molde": "5436",
            "cbr_volume_molde": "3210",
            "cbr_numero_camadas": "5",
            "cbr_golpes_camada": "26",
            "cbr_peso_soquete": "4536",
            "cbr_espessura_disco": '2½"',
            "cbr_altura_cilindro": "114",
            "cbr_constante_prensa": "0,0839",
            "umidade_otima": "9.8",
            "densidade_maxima": "1.958",
            "cbr": "34",
            "expansao": "0.5",
        }
    )
    assert form.is_valid()
    assert empty_review_fields(form, form.cleaned_data) == []


@pytest.mark.django_db
def test_upload_rejects_more_than_three_files(client):
    files = [
        SimpleUploadedFile(f"ensaio_{index}.jpg", b"fake-image", content_type="image/jpeg")
        for index in range(4)
    ]
    response = client.post(
        reverse("ensaios:upload_post"),
        {
            "language": "pt",
            "expected_test_type": "auto",
            "files": files,
        },
    )
    assert response.status_code == 200
    assert "Envie no máximo 3 arquivos por ensaio" in response.content.decode()


@pytest.mark.django_db
@override_settings(OPENAI_API_KEY="", MEDIA_ROOT=None)
def test_upload_review_generate_download_flow(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    upload = SimpleUploadedFile("ensaio.jpg", b"fake-image", content_type="image/jpeg")
    response = client.post(
        reverse("ensaios:upload_post"),
        {
            "expected_test_type": "auto",
            "language": "pt",
            "files": [upload],
        },
    )
    assert response.status_code == 302
    job = Job.objects.get()
    assert job.status == Job.STATUS_REVIEW_PENDING
    extracted = job.extracted_data
    extracted["compactacao"]["pontos"] = [
        {
            "ponto": 1,
            "peso_umido_molde_g": 9374,
            "peso_solo_umido_g": 3960,
            "umidade_media_percent": 3.5,
            "densidade_seca_g_cm3": 1.85,
        },
        {
            "ponto": 2,
            "peso_umido_molde_g": 9874,
            "peso_solo_umido_g": 4460,
            "umidade_media_percent": 9.8,
            "densidade_seca_g_cm3": 1.958,
        },
    ]
    extracted["cbr"]["leituras"] = [
        {"linha": 29, "leitura_extensometro": 282, "pressao_corrigida_kg_cm2": 273.5, "cbr_percent": 34}
    ]
    job.extracted_data = extracted
    job.save()

    response = client.post(
        reverse("ensaios:review", args=[job.id]),
        {
            "test_type": "ambos",
            "language": "pt",
            "proctor_interessado": "PREFEITURA",
            "proctor_obra": "AV. BEIRA MAR",
            "proctor_energia": "INTERMEDIÁRIO",
            "proctor_estaca": "ESTACA 02",
            "proctor_data_ensaio": "2026-07-08",
            "cbr_registro": "102-CBR",
            "cbr_molde_numero": "03",
            "cbr_peso_molde": "5436",
            "cbr_volume_molde": "3210",
            "cbr_numero_camadas": "5",
            "cbr_golpes_camada": "26",
            "cbr_peso_soquete": "4536",
            "cbr_espessura_disco": "2,5",
            "cbr_altura_cilindro": "114",
            "cbr_constante_prensa": "0,0839",
            "gran_empresa_executora": "RCA",
            "gran_obra": "AV. BEIRA MAR",
            "gran_estaca": "ESTACA 02",
            "gran_data_ensaio": "2026-07-08",
            "umidade_otima": "9.8",
            "densidade_maxima": "1.958",
            "cbr": "34",
            "expansao": "0.5",
            "passante_10": "25.5",
            "passante_40": "19.7",
            "passante_200": "11.4",
            "classificacao_trb": "A-1-a",
            "classificacao_sucs": "GM",
            "ll": "NL",
            "lp": "NP",
            "ip": "NP",
        },
    )
    assert response.status_code == 302

    response = client.post(reverse("ensaios:generate", args=[job.id]))
    assert response.status_code == 302
    job.refresh_from_db()
    assert job.status == Job.STATUS_DONE
    assert len(job.output_files) == 2

    response = client.get(reverse("ensaios:download", args=[job.id, 0]))
    assert response.status_code == 200
