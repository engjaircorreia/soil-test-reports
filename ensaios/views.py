from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CBR_EQUIPMENT_DEFAULTS, ReviewForm, UploadForm
from .models import Job
from .services.extraction_openai import extract_data
from .services.pipeline import build_review_payload
from .services.workbook_fill import generate_workbooks


PROCTOR_ADMIN_FIELDS = {
    "interessado": "proctor_interessado",
    "obra": "proctor_obra",
    "proctor": "proctor_energia",
    "registro": "proctor_registro",
    "estaca": "proctor_estaca",
    "profundidade": "proctor_profundidade",
    "data_ensaio": "proctor_data_ensaio",
    "procedencia": "proctor_procedencia",
    "cidade": "proctor_cidade",
    "responsavel_tecnico": "proctor_responsavel_tecnico",
    "observacoes": "proctor_observacoes",
}

CBR_ADMIN_FIELDS = {
    "registro": "cbr_registro",
    "molde_numero": "cbr_molde_numero",
    "peso_molde": "cbr_peso_molde",
    "volume_molde": "cbr_volume_molde",
    "numero_camadas": "cbr_numero_camadas",
    "golpes_camada": "cbr_golpes_camada",
    "peso_soquete": "cbr_peso_soquete",
    "espessura_disco": "cbr_espessura_disco",
    "altura_cilindro": "cbr_altura_cilindro",
    "constante_prensa": "cbr_constante_prensa",
}

GRANULOMETRY_ADMIN_FIELDS = {
    "empresa_executora": "gran_empresa_executora",
    "obra": "gran_obra",
    "procedencia": "gran_procedencia",
    "camada": "gran_camada",
    "estaca": "gran_estaca",
    "lado": "gran_lado",
    "profundidade": "gran_profundidade",
    "data_ensaio": "gran_data_ensaio",
    "laboratorio": "gran_laboratorio",
    "operador": "gran_operador",
    "laboratorista": "gran_laboratorista",
    "registro": "gran_registro",
}

COMPACTION_REVIEW_FIELDS = [
    *PROCTOR_ADMIN_FIELDS.values(),
    *CBR_ADMIN_FIELDS.values(),
    "umidade_otima",
    "densidade_maxima",
    "cbr",
    "expansao",
]

GRANULOMETRY_REVIEW_FIELDS = [
    *GRANULOMETRY_ADMIN_FIELDS.values(),
    "passante_10",
    "passante_40",
    "passante_200",
    "classificacao_trb",
    "classificacao_sucs",
    "ll",
    "lp",
    "ip",
]

OPTIONAL_EMPTY_WARNING_FIELDS = {"proctor_observacoes"}


def serialize_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value or ""


def admin_data_from_cleaned(cleaned: dict) -> dict:
    data = {
        "expected_test_type": cleaned.get("expected_test_type") or "auto",
        "language": cleaned.get("language") or "pt",
        "test_type": cleaned.get("test_type") or cleaned.get("expected_test_type") or "ambos",
    }
    data.update({
        "proctor_admin": block_from_cleaned(cleaned, PROCTOR_ADMIN_FIELDS),
        "cbr_admin": cbr_block_from_cleaned(cleaned),
        "granulometria_admin": block_from_cleaned(cleaned, GRANULOMETRY_ADMIN_FIELDS),
    })
    return add_flat_compatibility(data)


def block_from_cleaned(cleaned: dict, mapping: dict[str, str]) -> dict:
    return {key: serialize_value(cleaned.get(field)) for key, field in mapping.items()}


def cbr_block_from_cleaned(cleaned: dict) -> dict:
    block = block_from_cleaned(cleaned, CBR_ADMIN_FIELDS)
    for key, default in CBR_EQUIPMENT_DEFAULTS.items():
        if block.get(key) in (None, ""):
            block[key] = default
    return block


def block_value(data: dict, block_name: str, key: str, default: str = ""):
    block = data.get(block_name)
    if isinstance(block, dict) and block.get(key) not in (None, ""):
        return block.get(key)
    if data.get(key) not in (None, ""):
        return data.get(key)
    return default


def initial_for_mapping(data: dict, block_name: str, mapping: dict[str, str]) -> dict:
    initial = {}
    today = timezone.localdate().isoformat()
    for key, field in mapping.items():
        initial[field] = block_value(data, block_name, key)
        if key == "data_ensaio" and not initial[field]:
            initial[field] = today
        if block_name == "cbr_admin" and key in CBR_EQUIPMENT_DEFAULTS and not initial[field]:
            initial[field] = CBR_EQUIPMENT_DEFAULTS[key]
    return initial


def add_flat_compatibility(reviewed: dict) -> dict:
    proctor = reviewed.get("proctor_admin") or {}
    cbr_admin = reviewed.get("cbr_admin") or {}
    granulometry = reviewed.get("granulometria_admin") or {}
    for key in {
        "interessado",
        "obra",
        "proctor",
        "registro",
        "estaca",
        "profundidade",
        "data_ensaio",
        "procedencia",
        "cidade",
        "responsavel_tecnico",
        "observacoes",
    }:
        reviewed[key] = proctor.get(key) or cbr_admin.get(key) or granulometry.get(key) or ""
    for key in {
        "empresa_executora",
        "camada",
        "lado",
        "laboratorio",
        "operador",
        "laboratorista",
    }:
        reviewed[key] = granulometry.get(key) or ""
    return reviewed


def review_initial(job: Job) -> dict:
    data = job.reviewed_data or job.extracted_data or {}
    compactacao = data.get("compactacao") or {}
    cbr = data.get("cbr") or {}
    granulometria = data.get("granulometria") or {}
    limites = granulometria.get("limites") or {}
    initial = {}
    initial.update(initial_for_mapping(data, "proctor_admin", PROCTOR_ADMIN_FIELDS))
    initial.update(initial_for_mapping(data, "cbr_admin", CBR_ADMIN_FIELDS))
    initial.update(initial_for_mapping(data, "granulometria_admin", GRANULOMETRY_ADMIN_FIELDS))
    initial.update({
        "language": data.get("language") or job.language,
        "test_type": data.get("test_type") or job.test_type,
        "umidade_otima": compactacao.get("umidade_otima"),
        "densidade_maxima": compactacao.get("densidade_maxima"),
        "cbr": cbr.get("cbr"),
        "expansao": cbr.get("expansao"),
        "passante_10": granulometria.get("passante_10"),
        "passante_40": granulometria.get("passante_40"),
        "passante_200": granulometria.get("passante_200"),
        "classificacao_trb": granulometria.get("classificacao_trb") or "",
        "classificacao_sucs": granulometria.get("classificacao_sucs") or "",
        "ll": limites.get("ll") or "NL",
        "lp": limites.get("lp") or "NP",
        "ip": limites.get("ip") or "NP",
    })
    return initial


def form_to_reviewed_data(cleaned: dict) -> dict:
    reviewed = admin_data_from_cleaned(cleaned)
    reviewed.update({
        "proctor_admin": block_from_cleaned(cleaned, PROCTOR_ADMIN_FIELDS),
        "cbr_admin": cbr_block_from_cleaned(cleaned),
        "granulometria_admin": block_from_cleaned(cleaned, GRANULOMETRY_ADMIN_FIELDS),
        "compactacao": {
            "umidade_otima": cleaned.get("umidade_otima"),
            "densidade_maxima": cleaned.get("densidade_maxima"),
            "pontos": [],
        },
        "cbr": {
            "cbr": cleaned.get("cbr"),
            "expansao": cleaned.get("expansao"),
            "leituras": [],
        },
        "granulometria": {
            "passante_10": cleaned.get("passante_10"),
            "passante_40": cleaned.get("passante_40"),
            "passante_200": cleaned.get("passante_200"),
            "classificacao_trb": cleaned.get("classificacao_trb") or "",
            "classificacao_sucs": cleaned.get("classificacao_sucs") or "",
            "limites": {
                "ll": cleaned.get("ll") or "NL",
                "lp": cleaned.get("lp") or "NP",
                "ip": cleaned.get("ip") or "NP",
            },
        },
        "warnings": [],
    })
    return add_flat_compatibility(reviewed)


def preserve_extracted_technical_details(reviewed: dict, extracted: dict | None) -> dict:
    extracted = extracted or {}
    for block_name, keys in {
        "compactacao": {"higroscopica", "pontos"},
        "cbr": {
            "higroscopica",
            "moldagem",
            "peso_solo_umido_passando_peneira_4",
            "calculo_moldagem",
            "verificacao_moldagem",
            "leituras",
        },
    }.items():
        source = extracted.get(block_name)
        target = reviewed.get(block_name)
        if not isinstance(source, dict) or not isinstance(target, dict):
            continue
        for key in keys:
            if target.get(key) in (None, "", []) and source.get(key) not in (None, "", []):
                target[key] = source.get(key)
    return reviewed


def empty_review_fields(form: ReviewForm, cleaned: dict) -> list[str]:
    test_type = cleaned.get("test_type") or "ambos"
    fields: list[str] = []
    if test_type in {"compactacao_cbr", "ambos"}:
        fields.extend(COMPACTION_REVIEW_FIELDS)
    if test_type in {"granulometria", "ambos"}:
        fields.extend(GRANULOMETRY_REVIEW_FIELDS)

    labels: list[str] = []
    seen = set()
    for field in fields:
        if field in seen or field in OPTIONAL_EMPTY_WARNING_FIELDS:
            continue
        seen.add(field)
        value = cleaned.get(field)
        if field.startswith("cbr_"):
            key = field.removeprefix("cbr_")
            if key in CBR_EQUIPMENT_DEFAULTS:
                value = value or CBR_EQUIPMENT_DEFAULTS[key]
        if value in (None, ""):
            labels.append(str(form.fields[field].label).replace(" *", ""))
    return labels


def upload_view(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            job = Job.objects.create(
                status=Job.STATUS_EXTRACTING,
                language=form.cleaned_data["language"],
                test_type=(
                    form.cleaned_data.get("expected_test_type")
                    if form.cleaned_data.get("expected_test_type") != "auto"
                    else "ambos"
                ),
            )
            storage = FileSystemStorage(location=settings.MEDIA_ROOT / "uploads")
            saved_files = []
            for file in form.cleaned_data["files"]:
                saved_name = storage.save(f"job_{job.id}/{file.name}", file)
                saved_files.append(
                    {
                        "name": file.name,
                        "path": str(settings.MEDIA_ROOT / "uploads" / saved_name),
                        "url": storage.url(saved_name),
                    }
                )

            initial = admin_data_from_cleaned(form.cleaned_data)
            extracted, raw = extract_data([item["path"] for item in saved_files], initial)
            payload = build_review_payload(extracted)
            job.original_files = saved_files
            job.extracted_data = payload["review_data"]
            job.openai_raw_response = raw
            job.test_type = job.extracted_data.get("test_type") or "ambos"
            job.status = Job.STATUS_REVIEW_PENDING
            job.save()
            return redirect("ensaios:review", job_id=job.id)
    else:
        form = UploadForm()
    return render(request, "ensaios/upload.html", {"form": form})


def review_view(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            reviewed = form_to_reviewed_data(form.cleaned_data)
            preserved = preserve_extracted_technical_details(reviewed, job.extracted_data)
            payload = build_review_payload(preserved)
            job.reviewed_data = payload["review_data"]
            job.language = form.cleaned_data["language"]
            job.test_type = form.cleaned_data["test_type"]
            job.status = Job.STATUS_REVIEW_PENDING
            job.save()
            empty_fields = empty_review_fields(form, form.cleaned_data)
            if empty_fields:
                messages.warning(
                    request,
                    "Campos ainda vazios: " + ", ".join(empty_fields) + ".",
                )
            return redirect("ensaios:review", job_id=job.id)
    else:
        form = ReviewForm(initial=review_initial(job))
    warnings = (job.extracted_data or {}).get("warnings") or []
    detected_files = (job.extracted_data or {}).get("arquivos") or []
    return render(
        request,
        "ensaios/review.html",
        {"form": form, "job": job, "warnings": warnings, "detected_files": detected_files},
    )


def generate_view(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if request.method != "POST":
        return redirect("ensaios:review", job_id=job.id)
    try:
        job.status = Job.STATUS_GENERATING
        job.save(update_fields=["status", "updated_at"])
        data = job.reviewed_data or job.extracted_data
        if not data:
            messages.error(request, "Revise os dados antes de gerar a planilha.")
            return redirect("ensaios:review", job_id=job.id)
        job.output_files = generate_workbooks(job.id, data)
        job.status = Job.STATUS_DONE
        job.error_message = ""
        job.save()
        messages.success(request, "Planilha gerada com sucesso.")
    except Exception as exc:
        job.status = Job.STATUS_ERROR
        job.error_message = str(exc)
        job.save()
        messages.error(request, f"Falha ao gerar planilha: {exc}")
        return redirect("ensaios:review", job_id=job.id)
    return redirect("ensaios:result", job_id=job.id)


def result_view(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    return render(request, "ensaios/result.html", {"job": job})


def download_view(request, job_id, file_index):
    job = get_object_or_404(Job, pk=job_id)
    try:
        item = job.output_files[file_index]
    except (IndexError, TypeError):
        raise Http404("Arquivo não encontrado.")
    path = Path(item["path"])
    if not path.exists():
        raise Http404("Arquivo não encontrado.")
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)

# Create your views here.
