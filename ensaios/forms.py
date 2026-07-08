from __future__ import annotations

from django import forms
from django.utils import timezone

from .models import Job


DATE_INPUT = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})

CBR_EQUIPMENT_DEFAULTS = {
    "molde_numero": "02",
    "peso_molde": "5436",
    "volume_molde": "3210",
    "numero_camadas": "5",
    "golpes_camada": "26",
    "peso_soquete": "4536",
    "espessura_disco": '2½"',
    "altura_cilindro": "114",
    "constante_prensa": "0,0839",
}

REQUIRED_DISPLAY_FIELDS = {
    "proctor_interessado",
    "proctor_obra",
    "proctor_energia",
    "proctor_estaca",
    "proctor_data_ensaio",
    "proctor_procedencia",
    "cbr_registro",
    "cbr_molde_numero",
    "cbr_peso_molde",
    "cbr_volume_molde",
    "cbr_numero_camadas",
    "cbr_golpes_camada",
    "cbr_peso_soquete",
    "cbr_espessura_disco",
    "cbr_altura_cilindro",
    "cbr_constante_prensa",
    "gran_empresa_executora",
    "gran_obra",
    "gran_procedencia",
    "gran_estaca",
    "gran_data_ensaio",
}

CALCULATED_REVIEW_FIELDS = {
    "umidade_otima",
    "densidade_maxima",
    "cbr",
    "expansao",
    "passante_10",
    "passante_40",
    "passante_200",
}


def decorate_fields(form: forms.Form) -> None:
    for name, field in form.fields.items():
        if name in REQUIRED_DISPLAY_FIELDS:
            if field.label and not str(field.label).endswith(" *"):
                field.label = f"{field.label} *"
            field.widget.attrs["data-required-field"] = "true"
        if name in CALCULATED_REVIEW_FIELDS:
            field.widget.attrs["readonly"] = "readonly"
            field.widget.attrs["data-calculated-field"] = "true"


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            return [super(MultipleFileField, self).clean(item, initial) for item in data]
        return [super().clean(data, initial)]


class UploadForm(forms.Form):
    expected_test_type = forms.ChoiceField(
        label="Tipo esperado",
        choices=[("auto", "Detectar automaticamente"), *Job.TEST_TYPE_CHOICES],
        initial="auto",
        required=False,
    )
    language = forms.ChoiceField(label="Idioma do modelo", choices=Job.LANGUAGE_CHOICES)
    proctor_interessado = forms.CharField(label="Interessado / contratante", max_length=160, required=False)
    proctor_obra = forms.CharField(label="Obra", max_length=160, required=False)
    proctor_energia = forms.ChoiceField(
        label="Energia Proctor",
        choices=[("INTERMEDIÁRIO", "Intermediário"), ("NORMAL", "Normal"), ("MODIFICADO", "Modificado")],
        required=False,
    )
    proctor_registro = forms.CharField(label="Registro nº", max_length=40, required=False)
    proctor_estaca = forms.CharField(label="Local / furo / estaca", max_length=80, required=False)
    proctor_profundidade = forms.CharField(label="Profundidade do furo", max_length=40, required=False)
    proctor_data_ensaio = forms.DateField(
        label="Data do ensaio",
        required=False,
        initial=timezone.localdate,
        input_formats=["%Y-%m-%d"],
        widget=DATE_INPUT,
    )
    proctor_procedencia = forms.CharField(label="Procedência / rua", max_length=160, required=False)
    proctor_cidade = forms.CharField(label="Cidade", max_length=120, required=False)
    proctor_responsavel_tecnico = forms.CharField(label="Responsável técnico", max_length=160, required=False)
    proctor_observacoes = forms.CharField(label="Observações", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    cbr_registro = forms.CharField(label="Registro nº do CBR", max_length=40, required=False)
    cbr_molde_numero = forms.CharField(label="Molde nº", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["molde_numero"])
    cbr_peso_molde = forms.CharField(label="Peso do molde (g)", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["peso_molde"])
    cbr_volume_molde = forms.CharField(label="Volume do molde (cm³)", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["volume_molde"])
    cbr_numero_camadas = forms.CharField(label="Número de camadas", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["numero_camadas"])
    cbr_golpes_camada = forms.CharField(label="Golpes por camada", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["golpes_camada"])
    cbr_peso_soquete = forms.CharField(label="Peso do soquete (g)", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["peso_soquete"])
    cbr_espessura_disco = forms.CharField(label="Espessura do disco espaçador", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["espessura_disco"])
    cbr_altura_cilindro = forms.CharField(label="Altura do cilindro (mm)", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["altura_cilindro"])
    cbr_constante_prensa = forms.CharField(label="Constante da prensa", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["constante_prensa"])

    gran_empresa_executora = forms.CharField(label="Empresa executora", max_length=160, required=False)
    gran_obra = forms.CharField(label="Obra", max_length=160, required=False)
    gran_procedencia = forms.CharField(label="Procedência / rua", max_length=160, required=False)
    gran_camada = forms.CharField(label="Camada", max_length=120, required=False)
    gran_estaca = forms.CharField(label="Local / furo / estaca", max_length=80, required=False)
    gran_lado = forms.CharField(label="Lado", max_length=40, required=False)
    gran_profundidade = forms.CharField(label="Profundidade do furo", max_length=40, required=False)
    gran_data_ensaio = forms.DateField(
        label="Data do ensaio",
        required=False,
        initial=timezone.localdate,
        input_formats=["%Y-%m-%d"],
        widget=DATE_INPUT,
    )
    gran_laboratorio = forms.CharField(label="Laboratório", max_length=160, required=False)
    gran_operador = forms.CharField(label="Operador", max_length=120, required=False)
    gran_laboratorista = forms.CharField(label="Laboratorista", max_length=120, required=False)
    gran_registro = forms.CharField(label="Registro nº", max_length=40, required=False)
    files = MultipleFileField(label="Arquivos", help_text="Envie até 3 imagens ou PDFs")

    allowed_extensions = {".jpg", ".jpeg", ".png", ".pdf"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        decorate_fields(self)

    def clean_files(self):
        files = self.cleaned_data["files"]
        if len(files) > 3:
            raise forms.ValidationError("Envie no máximo 3 arquivos por ensaio.")
        for file in files:
            suffix = "." + file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
            if suffix not in self.allowed_extensions:
                raise forms.ValidationError("Envie apenas arquivos JPG, PNG ou PDF.")
            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError("Cada arquivo deve ter no máximo 20 MB.")
        return files


class ReviewForm(forms.Form):
    language = forms.ChoiceField(label="Idioma do modelo", choices=Job.LANGUAGE_CHOICES)
    test_type = forms.ChoiceField(label="Tipo de ensaio", choices=Job.TEST_TYPE_CHOICES)

    proctor_interessado = forms.CharField(label="Interessado / contratante", max_length=160, required=False)
    proctor_obra = forms.CharField(label="Obra", max_length=160, required=False)
    proctor_energia = forms.ChoiceField(
        label="Energia Proctor",
        choices=[("INTERMEDIÁRIO", "Intermediário"), ("NORMAL", "Normal"), ("MODIFICADO", "Modificado")],
        required=False,
    )
    proctor_registro = forms.CharField(label="Registro nº", max_length=40, required=False)
    proctor_estaca = forms.CharField(label="Local / furo / estaca", max_length=80, required=False)
    proctor_profundidade = forms.CharField(label="Profundidade do furo", max_length=40, required=False)
    proctor_data_ensaio = forms.DateField(
        label="Data do ensaio",
        required=False,
        initial=timezone.localdate,
        input_formats=["%Y-%m-%d"],
        widget=DATE_INPUT,
    )
    proctor_procedencia = forms.CharField(label="Procedência / rua", max_length=160, required=False)
    proctor_cidade = forms.CharField(label="Cidade", max_length=120, required=False)
    proctor_responsavel_tecnico = forms.CharField(label="Responsável técnico", max_length=160, required=False)
    proctor_observacoes = forms.CharField(label="Observações", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    umidade_otima = forms.FloatField(label="Umidade ótima (%)", required=False)
    densidade_maxima = forms.FloatField(label="Densidade máxima (g/cm³)", required=False)

    cbr_registro = forms.CharField(label="Registro nº do CBR", max_length=40, required=False)
    cbr_molde_numero = forms.CharField(label="Molde nº", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["molde_numero"])
    cbr_peso_molde = forms.CharField(label="Peso do molde (g)", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["peso_molde"])
    cbr_volume_molde = forms.CharField(label="Volume do molde (cm³)", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["volume_molde"])
    cbr_numero_camadas = forms.CharField(label="Número de camadas", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["numero_camadas"])
    cbr_golpes_camada = forms.CharField(label="Golpes por camada", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["golpes_camada"])
    cbr_peso_soquete = forms.CharField(label="Peso do soquete (g)", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["peso_soquete"])
    cbr_espessura_disco = forms.CharField(label="Espessura do disco espaçador", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["espessura_disco"])
    cbr_altura_cilindro = forms.CharField(label="Altura do cilindro (mm)", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["altura_cilindro"])
    cbr_constante_prensa = forms.CharField(label="Constante da prensa", max_length=40, required=False, initial=CBR_EQUIPMENT_DEFAULTS["constante_prensa"])
    cbr = forms.FloatField(label="CBR (%)", required=False)
    expansao = forms.FloatField(label="Expansão (%)", required=False)

    gran_empresa_executora = forms.CharField(label="Empresa executora", max_length=160, required=False)
    gran_obra = forms.CharField(label="Obra", max_length=160, required=False)
    gran_procedencia = forms.CharField(label="Procedência / rua", max_length=160, required=False)
    gran_camada = forms.CharField(label="Camada", max_length=120, required=False)
    gran_estaca = forms.CharField(label="Local / furo / estaca", max_length=80, required=False)
    gran_lado = forms.CharField(label="Lado", max_length=40, required=False)
    gran_profundidade = forms.CharField(label="Profundidade do furo", max_length=40, required=False)
    gran_data_ensaio = forms.DateField(
        label="Data do ensaio",
        required=False,
        initial=timezone.localdate,
        input_formats=["%Y-%m-%d"],
        widget=DATE_INPUT,
    )
    gran_laboratorio = forms.CharField(label="Laboratório", max_length=160, required=False)
    gran_operador = forms.CharField(label="Operador", max_length=120, required=False)
    gran_laboratorista = forms.CharField(label="Laboratorista", max_length=120, required=False)
    gran_registro = forms.CharField(label="Registro nº", max_length=40, required=False)
    passante_10 = forms.FloatField(label="Passante #10 (%)", required=False)
    passante_40 = forms.FloatField(label="Passante #40 (%)", required=False)
    passante_200 = forms.FloatField(label="Passante #200 (%)", required=False)
    classificacao_trb = forms.CharField(label="Classificação TRB", required=False, max_length=40)
    classificacao_sucs = forms.CharField(label="Classificação SUCS", required=False, max_length=40)
    ll = forms.CharField(label="LL", required=False, max_length=20)
    lp = forms.CharField(label="LP", required=False, max_length=20)
    ip = forms.CharField(label="IP", required=False, max_length=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        decorate_fields(self)
