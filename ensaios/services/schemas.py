from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _compact_dict(data: dict[str, Any]) -> dict[str, Any]:
    compacted: dict[str, Any] = {}
    for key, value in data.items():
        if is_dataclass(value):
            compacted[key] = _compact_dict(asdict(value))
        elif isinstance(value, dict):
            compacted[key] = _compact_dict(value)
        elif isinstance(value, list):
            compacted[key] = [
                _compact_dict(asdict(item)) if is_dataclass(item) else item
                for item in value
            ]
        else:
            compacted[key] = value
    return compacted


@dataclass
class ValidationIssue:
    field: str | None = None
    message: str | None = None
    severity: str = "warning"
    test_type: str | None = None
    code: str | None = None


@dataclass
class UploadedFileClassification:
    nome: str | None = None
    tipo_detectado: str | None = None
    confianca: float | int | str | None = None
    observacoes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UploadedFileClassification":
        return cls(
            nome=data.get("nome") or data.get("name"),
            tipo_detectado=data.get("tipo_detectado") or data.get("classificacao"),
            confianca=data.get("confianca"),
            observacoes=data.get("observacoes"),
        )


@dataclass
class Metadata:
    idioma_modelo: str | None = None
    tipo_esperado: str | None = None
    arquivos: list[UploadedFileClassification] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "Metadata":
        root = root or {}
        file_items = data.get("arquivos", root.get("arquivos", []))
        return cls(
            idioma_modelo=data.get("idioma_modelo") or root.get("language"),
            tipo_esperado=data.get("tipo_esperado") or root.get("expected_test_type") or root.get("test_type"),
            arquivos=[
                UploadedFileClassification.from_dict(item)
                for item in _as_list(file_items)
                if isinstance(item, dict)
            ],
        )


@dataclass
class DadosComuns:
    interessado: str | None = None
    obra: str | None = None
    procedencia_rua: str | None = None
    cidade: str | None = None
    local_furo_estaca: str | None = None
    profundidade_furo: str | None = None
    data_ensaio: str | None = None
    registro_numero: str | None = None
    responsavel_tecnico: str | None = None
    observacoes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "DadosComuns":
        root = root or {}
        return cls(
            interessado=data.get("interessado") or root.get("interessado"),
            obra=data.get("obra") or root.get("obra"),
            procedencia_rua=data.get("procedencia_rua") or data.get("procedencia") or root.get("procedencia"),
            cidade=data.get("cidade") or root.get("cidade"),
            local_furo_estaca=data.get("local_furo_estaca") or data.get("estaca") or root.get("estaca"),
            profundidade_furo=data.get("profundidade_furo") or data.get("profundidade") or root.get("profundidade"),
            data_ensaio=data.get("data_ensaio") or root.get("data_ensaio"),
            registro_numero=data.get("registro_numero") or data.get("registro") or root.get("registro"),
            responsavel_tecnico=data.get("responsavel_tecnico") or root.get("responsavel_tecnico"),
            observacoes=data.get("observacoes") or root.get("observacoes"),
        )


@dataclass
class MoistureBlockRaw:
    capsula: str | None = None
    peso_bruto_umido_g: float | int | str | None = None
    peso_bruto_seco_g: float | int | str | None = None
    tara_capsula_g: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MoistureBlockRaw":
        return cls(
            capsula=data.get("capsula"),
            peso_bruto_umido_g=data.get("peso_bruto_umido_g", data.get("peso_bruto_umido")),
            peso_bruto_seco_g=data.get("peso_bruto_seco_g", data.get("peso_bruto_seco")),
            tara_capsula_g=data.get("tara_capsula_g", data.get("tara_capsula")),
        )


@dataclass
class ProctorPointRaw:
    ponto: int | str | None = None
    peso_solo_umido_molde_g: float | int | str | None = None
    peso_solo_umido_g: float | int | str | None = None
    capsulas: list[MoistureBlockRaw] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProctorPointRaw":
        return cls(
            ponto=data.get("ponto"),
            peso_solo_umido_molde_g=data.get("peso_solo_umido_molde_g")
            or data.get("peso_umido_molde_g"),
            peso_solo_umido_g=data.get("peso_solo_umido_g"),
            capsulas=[
                MoistureBlockRaw.from_dict(item)
                for item in _as_list(data.get("capsulas"))
                if isinstance(item, dict)
            ],
        )


@dataclass
class ProctorReadResult:
    umidade_otima_percent: float | int | str | None = None
    densidade_maxima_g_cm3: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProctorReadResult":
        return cls(
            umidade_otima_percent=data.get("umidade_otima_percent", data.get("umidade_otima")),
            densidade_maxima_g_cm3=data.get("densidade_maxima_g_cm3", data.get("densidade_maxima")),
        )


@dataclass
class ProctorRaw:
    energia: str | None = None
    molde_numero: str | None = None
    peso_molde_g: float | int | str | None = None
    volume_molde_cm3: float | int | str | None = None
    numero_camadas: float | int | str | None = None
    golpes_por_camada: float | int | str | None = None
    peso_soquete_g: float | int | str | None = None
    higroscopica: MoistureBlockRaw = field(default_factory=MoistureBlockRaw)
    pontos: list[ProctorPointRaw] = field(default_factory=list)
    resultado_lido: ProctorReadResult = field(default_factory=ProctorReadResult)

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "ProctorRaw":
        root = root or {}
        admin = _as_dict(root.get("proctor_admin"))
        return cls(
            energia=data.get("energia") or root.get("proctor") or admin.get("proctor"),
            molde_numero=data.get("molde_numero"),
            peso_molde_g=data.get("peso_molde_g"),
            volume_molde_cm3=data.get("volume_molde_cm3"),
            numero_camadas=data.get("numero_camadas"),
            golpes_por_camada=data.get("golpes_por_camada"),
            peso_soquete_g=data.get("peso_soquete_g"),
            higroscopica=MoistureBlockRaw.from_dict(_as_dict(data.get("higroscopica"))),
            pontos=[
                ProctorPointRaw.from_dict(item)
                for item in _as_list(data.get("pontos"))
                if isinstance(item, dict)
            ],
            resultado_lido=ProctorReadResult.from_dict(
                _as_dict(data.get("resultado_lido")) or data
            ),
        )


@dataclass
class CbrMoldingCalculationRaw:
    peso_solo_umido_passando_peneira_4_g: float | int | str | None = None
    peso_solo_seco_passando_peneira_4_g: float | int | str | None = None
    peso_pedregulho_retido_peneira_4_g: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "CbrMoldingCalculationRaw":
        root = root or {}
        return cls(
            peso_solo_umido_passando_peneira_4_g=data.get(
                "peso_solo_umido_passando_peneira_4_g",
                root.get("peso_solo_umido_passando_peneira_4"),
            ),
            peso_solo_seco_passando_peneira_4_g=data.get(
                "peso_solo_seco_passando_peneira_4_g",
                data.get("peso_passando_peneira_4"),
            ),
            peso_pedregulho_retido_peneira_4_g=data.get(
                "peso_pedregulho_retido_peneira_4_g",
                data.get("peso_retido_peneira_4"),
            ),
        )


@dataclass
class CbrPenetrationRaw:
    tempo_min: float | int | str | None = None
    leitura_extensometro: float | int | str | None = None
    pressao_corrigida_kg_cm2: float | int | str | None = None
    penetracao_mm: float | int | str | None = None
    cbr_percent: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CbrPenetrationRaw":
        return cls(
            tempo_min=data.get("tempo_min"),
            leitura_extensometro=data.get("leitura_extensometro"),
            pressao_corrigida_kg_cm2=data.get("pressao_corrigida_kg_cm2"),
            penetracao_mm=data.get("penetracao_mm"),
            cbr_percent=data.get("cbr_percent"),
        )


@dataclass
class CbrExpansionRaw:
    leitura_inicial_mm: float | int | str | None = None
    leitura_final_mm: float | int | str | None = None
    expansao_percent_lida: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "CbrExpansionRaw":
        root = root or {}
        return cls(
            leitura_inicial_mm=data.get("leitura_inicial_mm"),
            leitura_final_mm=data.get("leitura_final_mm"),
            expansao_percent_lida=data.get("expansao_percent_lida", root.get("expansao")),
        )


@dataclass
class CbrMoldingCheckRaw:
    peso_bruto_umido_cp_molde_kg: float | int | str | None = None
    peso_cp_umido_kg: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CbrMoldingCheckRaw":
        return cls(
            peso_bruto_umido_cp_molde_kg=data.get(
                "peso_bruto_umido_cp_molde_kg",
                data.get("peso_bruto_cp_umido"),
            ),
            peso_cp_umido_kg=data.get("peso_cp_umido_kg", data.get("peso_cp_umido")),
        )


@dataclass
class CbrReadResult:
    cbr_percent: float | int | str | None = None
    expansao_percent: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "CbrReadResult":
        root = root or {}
        return cls(
            cbr_percent=data.get("cbr_percent", root.get("cbr")),
            expansao_percent=data.get("expansao_percent", root.get("expansao")),
        )


@dataclass
class CbrRaw:
    registro_numero_cbr: str | None = None
    molde_numero: str | None = None
    peso_molde_g: float | int | str | None = None
    volume_molde_cm3: float | int | str | None = None
    numero_camadas: float | int | str | None = None
    golpes_por_camada: float | int | str | None = None
    peso_soquete_g: float | int | str | None = None
    espessura_disco_espacador: str | None = None
    altura_cilindro_mm: float | int | str | None = None
    constante_prensa: float | int | str | None = None
    higroscopica: MoistureBlockRaw = field(default_factory=MoistureBlockRaw)
    moldagem: MoistureBlockRaw = field(default_factory=MoistureBlockRaw)
    calculo_moldagem: CbrMoldingCalculationRaw = field(default_factory=CbrMoldingCalculationRaw)
    penetracao: list[CbrPenetrationRaw] = field(default_factory=list)
    expansao: CbrExpansionRaw = field(default_factory=CbrExpansionRaw)
    verificacao_moldagem: CbrMoldingCheckRaw = field(default_factory=CbrMoldingCheckRaw)
    resultado_lido: CbrReadResult = field(default_factory=CbrReadResult)

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "CbrRaw":
        root = root or {}
        admin = _as_dict(root.get("cbr_admin"))
        return cls(
            registro_numero_cbr=data.get("registro_numero_cbr") or admin.get("registro"),
            molde_numero=data.get("molde_numero") or admin.get("molde_numero"),
            peso_molde_g=data.get("peso_molde_g") or admin.get("peso_molde"),
            volume_molde_cm3=data.get("volume_molde_cm3") or admin.get("volume_molde"),
            numero_camadas=data.get("numero_camadas") or admin.get("numero_camadas"),
            golpes_por_camada=data.get("golpes_por_camada") or admin.get("golpes_camada"),
            peso_soquete_g=data.get("peso_soquete_g") or admin.get("peso_soquete"),
            espessura_disco_espacador=data.get("espessura_disco_espacador") or admin.get("espessura_disco"),
            altura_cilindro_mm=data.get("altura_cilindro_mm") or admin.get("altura_cilindro"),
            constante_prensa=data.get("constante_prensa") or admin.get("constante_prensa"),
            higroscopica=MoistureBlockRaw.from_dict(_as_dict(data.get("higroscopica"))),
            moldagem=MoistureBlockRaw.from_dict(_as_dict(data.get("moldagem"))),
            calculo_moldagem=CbrMoldingCalculationRaw.from_dict(
                _as_dict(data.get("calculo_moldagem")),
                data,
            ),
            penetracao=[
                CbrPenetrationRaw.from_dict(item)
                for item in _as_list(data.get("penetracao", data.get("leituras")))
                if isinstance(item, dict)
            ],
            expansao=CbrExpansionRaw.from_dict(_as_dict(data.get("expansao")), data),
            verificacao_moldagem=CbrMoldingCheckRaw.from_dict(
                _as_dict(data.get("verificacao_moldagem"))
            ),
            resultado_lido=CbrReadResult.from_dict(_as_dict(data.get("resultado_lido")), data),
        )


@dataclass
class GranulometrySampleRaw:
    peso_umido_total_g: float | int | str | None = None
    peso_seco_total_g: float | int | str | None = None
    material_retido_2mm_g: float | int | str | None = None
    material_passante_2mm_g: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GranulometrySampleRaw":
        return cls(
            peso_umido_total_g=data.get("peso_umido_total_g"),
            peso_seco_total_g=data.get("peso_seco_total_g"),
            material_retido_2mm_g=data.get("material_retido_2mm_g"),
            material_passante_2mm_g=data.get("material_passante_2mm_g"),
        )


@dataclass
class SieveRaw:
    peneira: str | None = None
    abertura_mm: float | int | str | None = None
    peso_retido_g: float | int | str | None = None
    percentual_passante: float | int | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SieveRaw":
        return cls(
            peneira=data.get("peneira"),
            abertura_mm=data.get("abertura_mm"),
            peso_retido_g=data.get("peso_retido_g"),
            percentual_passante=data.get("percentual_passante"),
        )


@dataclass
class LimitsRaw:
    limite_liquidez: str | float | int | None = None
    limite_plasticidade: str | float | int | None = None
    indice_plasticidade: str | float | int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LimitsRaw":
        return cls(
            limite_liquidez=data.get("limite_liquidez", data.get("ll")),
            limite_plasticidade=data.get("limite_plasticidade", data.get("lp")),
            indice_plasticidade=data.get("indice_plasticidade", data.get("ip")),
        )


@dataclass
class ClassificationRaw:
    trb: str | None = None
    sucs: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "ClassificationRaw":
        root = root or {}
        return cls(
            trb=data.get("trb") or root.get("classificacao_trb"),
            sucs=data.get("sucs") or root.get("classificacao_sucs"),
        )


@dataclass
class GranulometriaRaw:
    empresa_executora: str | None = None
    obra: str | None = None
    procedencia_rua: str | None = None
    camada: str | None = None
    lado: str | None = None
    local_furo_estaca: str | None = None
    profundidade_furo: str | None = None
    data_ensaio: str | None = None
    laboratorio: str | None = None
    operador: str | None = None
    laboratorista: str | None = None
    registro_numero: str | None = None
    umidade: MoistureBlockRaw = field(default_factory=MoistureBlockRaw)
    amostra_total: GranulometrySampleRaw = field(default_factory=GranulometrySampleRaw)
    peneiras: list[SieveRaw] = field(default_factory=list)
    limites: LimitsRaw = field(default_factory=LimitsRaw)
    classificacao_lida: ClassificationRaw = field(default_factory=ClassificationRaw)

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: dict[str, Any] | None = None) -> "GranulometriaRaw":
        root = root or {}
        admin = _as_dict(root.get("granulometria_admin"))
        return cls(
            empresa_executora=data.get("empresa_executora") or root.get("empresa_executora") or admin.get("empresa_executora"),
            obra=data.get("obra") or root.get("obra") or admin.get("obra"),
            procedencia_rua=data.get("procedencia_rua") or data.get("procedencia") or root.get("procedencia") or admin.get("procedencia"),
            camada=data.get("camada") or root.get("camada") or admin.get("camada"),
            lado=data.get("lado") or root.get("lado") or admin.get("lado"),
            local_furo_estaca=data.get("local_furo_estaca") or data.get("estaca") or root.get("estaca") or admin.get("estaca"),
            profundidade_furo=data.get("profundidade_furo") or data.get("profundidade") or root.get("profundidade") or admin.get("profundidade"),
            data_ensaio=data.get("data_ensaio") or root.get("data_ensaio") or admin.get("data_ensaio"),
            laboratorio=data.get("laboratorio") or root.get("laboratorio") or admin.get("laboratorio"),
            operador=data.get("operador") or root.get("operador") or admin.get("operador"),
            laboratorista=data.get("laboratorista") or root.get("laboratorista") or admin.get("laboratorista"),
            registro_numero=data.get("registro_numero") or data.get("registro") or root.get("registro") or admin.get("registro"),
            umidade=MoistureBlockRaw.from_dict(_as_dict(data.get("umidade"))),
            amostra_total=GranulometrySampleRaw.from_dict(_as_dict(data.get("amostra_total"))),
            peneiras=[
                SieveRaw.from_dict(item)
                for item in _as_list(data.get("peneiras"))
                if isinstance(item, dict)
            ],
            limites=LimitsRaw.from_dict(_as_dict(data.get("limites"))),
            classificacao_lida=ClassificationRaw.from_dict(
                _as_dict(data.get("classificacao_lida")),
                data,
            ),
        )


@dataclass
class ProctorCalculated:
    points: list[dict[str, Any]] = field(default_factory=list)
    umidade_otima_percent: float | int | None = None
    densidade_maxima_g_cm3: float | int | None = None
    issues: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CbrCalculated:
    higroscopica: dict[str, Any] = field(default_factory=dict)
    moldagem: dict[str, Any] = field(default_factory=dict)
    penetracao: list[dict[str, Any]] = field(default_factory=list)
    cbr_percent: float | int | None = None
    expansao_percent: float | int | None = None
    issues: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GranulometriaCalculated:
    peneiras: list[dict[str, Any]] = field(default_factory=list)
    passante_10_percent: float | int | None = None
    passante_40_percent: float | int | None = None
    passante_200_percent: float | int | None = None
    issues: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ExtractionBundle:
    metadata: Metadata = field(default_factory=Metadata)
    dados_comuns: DadosComuns = field(default_factory=DadosComuns)
    proctor: ProctorRaw = field(default_factory=ProctorRaw)
    cbr: CbrRaw = field(default_factory=CbrRaw)
    granulometria: GranulometriaRaw = field(default_factory=GranulometriaRaw)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ReviewedBundle:
    metadata: Metadata = field(default_factory=Metadata)
    dados_comuns: DadosComuns = field(default_factory=DadosComuns)
    proctor: ProctorRaw = field(default_factory=ProctorRaw)
    cbr: CbrRaw = field(default_factory=CbrRaw)
    granulometria: GranulometriaRaw = field(default_factory=GranulometriaRaw)
    calculated: dict[str, Any] = field(default_factory=dict)
    validation_issues: list[ValidationIssue] = field(default_factory=list)


def extraction_bundle_from_dict(data: dict[str, Any] | None) -> ExtractionBundle:
    data = data or {}
    metadata_data = _as_dict(data.get("metadata"))
    dados_comuns_data = _as_dict(data.get("dados_comuns"))
    proctor_data = _as_dict(data.get("proctor") or data.get("compactacao"))
    cbr_data = _as_dict(data.get("cbr"))
    granulometria_data = _as_dict(data.get("granulometria"))
    return ExtractionBundle(
        metadata=Metadata.from_dict(metadata_data, data),
        dados_comuns=DadosComuns.from_dict(dados_comuns_data, data),
        proctor=ProctorRaw.from_dict(proctor_data, data),
        cbr=CbrRaw.from_dict(cbr_data, data),
        granulometria=GranulometriaRaw.from_dict(granulometria_data, data),
        warnings=[str(item) for item in _as_list(data.get("warnings"))],
    )


def extraction_bundle_to_dict(bundle: ExtractionBundle | dict[str, Any]) -> dict[str, Any]:
    if isinstance(bundle, dict):
        bundle = extraction_bundle_from_dict(bundle)
    return _compact_dict(asdict(bundle))


def reviewed_bundle_from_dict(data: dict[str, Any] | None) -> ReviewedBundle:
    bundle = extraction_bundle_from_dict(data)
    data = data or {}
    return ReviewedBundle(
        metadata=bundle.metadata,
        dados_comuns=bundle.dados_comuns,
        proctor=bundle.proctor,
        cbr=bundle.cbr,
        granulometria=bundle.granulometria,
        calculated=_as_dict(data.get("calculated_data") or data.get("calculated")),
        validation_issues=[
            ValidationIssue(**item)
            for item in _as_list(data.get("validation_issues"))
            if isinstance(item, dict)
        ],
    )


def reviewed_bundle_to_dict(bundle: ReviewedBundle | dict[str, Any]) -> dict[str, Any]:
    if isinstance(bundle, dict):
        bundle = reviewed_bundle_from_dict(bundle)
    return _compact_dict(asdict(bundle))
