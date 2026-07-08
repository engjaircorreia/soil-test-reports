from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

from django.conf import settings


EXTRACTION_PROMPT = """
Você é um laboratorista especialista em ensaios de solos. Sua tarefa é ler fotos/PDFs de fichas preenchidas à mão e devolver somente os dados técnicos necessários para preencher modelos Excel de Proctor/compactação, CBR e granulometria.

REGRAS GERAIS
- Responda somente com JSON válido, sem markdown.
- Use null quando o valor estiver ilegível, ausente ou ambíguo. Nunca invente resultado técnico.
- Nao calcule resultados técnicos. A IA deve apenas extrair dados brutos que estejam visíveis na ficha.
- Nao inferir valores ausentes a partir de outros campos. Se nao leu com seguranca, retorne null.
- A IA nao deve usar dados padrao de equipamento. Dados padrao serão aplicados pelo sistema quando existirem no formulario.
- A IA nao deve criar pontos de compactacao. Extraia somente pontos efetivamente visíveis.
- A IA nao deve sintetizar leituras de penetracao a partir do CBR final.
- A IA nao deve usar resultado final para preencher dados brutos.
- Preserve os dados administrativos enviados pelo usuário nos "Dados iniciais"; só substitua um dado administrativo se ele estiver vazio e a ficha mostrar esse dado com clareza.
- Classifique cada arquivo individualmente em "proctor", "cbr", "granulometria" ou "desconhecido" no campo metadata.arquivos[].tipo_detectado.
- Se houver "expected_test_type", use apenas como pista. A classificação visual dos arquivos deve prevalecer.
- Defina "test_type": "compactacao_cbr" quando houver compactação e/ou CBR; "granulometria" quando houver somente granulometria; "ambos" quando houver compactação/CBR e granulometria.
- Use vírgula ou ponto como separador decimal, mas retorne números JSON com ponto decimal.
- Não confunda pesos em gramas, leituras de relógio, pressões, cargas padrão ou massas retidas com percentuais finais.
- Quando encontrar um valor acompanhado de unidade incompatível, inclua warning e retorne null para o campo final.
- Além dos resultados finais, extraia os pesos brutos das umidades quando estiverem legíveis, pois eles alimentam fórmulas do Excel.

ORDEM DE PRIORIDADE ENTRE ARQUIVOS
- Para "compactacao.umidade_otima" e "compactacao.densidade_maxima", prefira a ficha de compactação/Proctor. Use dados repetidos na ficha CBR apenas como conferência ou fallback se a ficha de compactação não existir.
- Para "cbr.cbr" e "cbr.expansao", prefira a ficha CBR.
- Para "granulometria.passante_10", "passante_40" e "passante_200", use somente a ficha de granulometria.
- Para limites, se a ficha indicar material sem limite/plasticidade, retorne LL="NL", LP="NP", IP="NP".

COMPACTAÇÃO / PROCTOR - COMO LER
Identificação visual comum: título com "COMPACTAÇÃO", "PROCTOR" ou tabela "DETERMINAÇÃO DA UMIDADE".
Campos finais necessários:
- compactacao.umidade_otima: procure primeiro no quadro superior direito, perto de "h =", "w =", "umidade ótima", "umid. ótima" ou "hot". É um percentual, normalmente entre 5 e 20. Exemplo visual: "h = 9,7" significa 9.7.
- compactacao.densidade_maxima: procure primeiro no quadro superior direito, perto de "γmáx", "Ymáx", "densidade máxima" ou "dens. máx.". É densidade seca máxima em g/cm³. Se o valor aparecer como 1951, 1907, 2012 etc., normalize para 1.951, 1.907, 2.012. Não retorne 1951.
- Se não houver quadro superior com resultados, use a tabela inferior: pegue a maior "densidade do solo seco" e a "umidade média" da mesma linha. Não use "densidade do solo úmido".
- A tabela inferior geralmente tem colunas "Ponto", "Peso bruto úmido", "Peso do solo úmido", "Densidade do solo úmido", "Determinação da umidade", "Umidade média %" e "Densidade do solo seco". A umidade ótima é associada ao maior valor da coluna "Densidade do solo seco".
- Não use valores de "cápsula nº", "peso da água", "peso bruto seco", "peso bruto úmido" ou "peso do molde" como resultado final.
- Se houver quadro "DETERMINAÇÃO DA UMIDADE HIGROSCÓPICA", extraia em proctor.higroscopica: cápsula nº, peso bruto úmido, peso bruto seco e tara/peso da cápsula. Se esse quadro estiver vazio, deixe null; não invente cápsula H1.
- A umidade higroscópica pode ser a mesma amostra usada em Proctor e CBR. Mesmo assim, extraia a coluna/bloco visível de cada ficha quando existir; o sistema fará a conciliação entre Proctor e CBR.
- Se houver 4 ou 5 pontos, isso é normal. Não estime ponto faltante; extraia apenas o resultado final visível.

CBR / ÍNDICE DE SUPORTE CALIFORNIA - COMO LER
Identificação visual comum: título "CBR", "I.S.C.", "ÍNDICE DE SUPORTE CALIFORNIA", "California Bearing Ratio" ou tabela "ENSAIO DE PENETRAÇÃO".
Campos finais necessários:
- cbr.cbr: procure primeiro o quadro da curva ou resultado final com "I.S.C.", "ISC", "CBR" ou "ÍNDICE DE SUPORTE". Esse valor é percentual, normalmente escrito como 32%, 41%, 70%, etc. Retorne só o número.
- Se não houver quadro final, use a tabela "ENSAIO DE PENETRAÇÃO" e procure a coluna de percentuais calculados/corrigidos. Não use a coluna "Padrão", que costuma conter números como 70, 105, 133, 161, 182; esses NÃO são CBR.
- Na tabela de penetração, não use "leitura do manômetro", "pressão", "deflectômetro", "tempo" ou "penetração" como CBR final.
- cbr.expansao: procure no quadro "EXPANSÃO DE AMOSTRA INUNDADA" ou "EXPANSÃO". O valor final geralmente está no fim da coluna "Expansão %" ou anotado perto da última linha. Retorne percentual, por exemplo 0.5, 1.1, 2.0. Não use leituras de deflectômetro em mm como percentual.
- Em algumas fichas CBR, a coluna "Expansão %" fica pouco preenchida e o resultado final é escrito à mão na extrema direita ou no rodapé do bloco de expansão. Se houver um único valor final destacado ali, como "1,1", "0,5" ou "2", use esse valor como cbr.expansao.
- Neste modelo de ficha, o resultado final de expansão também pode aparecer na coluna "Diferença mm", na última linha preenchida do bloco de expansão, com valores como 0,5, 1,1 ou 2. Quando a coluna "Expansão %" estiver vazia, use esse valor final de "Diferença mm" como cbr.expansao e registre a evidência.
- A parte superior esquerda da ficha CBR pode repetir "densidade máxima" e "umidade ótima" da compactação. Use esses valores só como conferência/fallback para compactação; eles não substituem o CBR final.
- Dados de equipamento como molde nº, peso do molde, volume do molde, nº de camadas, golpes/camada, peso do soquete, disco espaçador, altura do cilindro e constante da prensa são dados administrativos/padrão quando vierem do formulário; não use esses números como resultado de CBR.
- No quadro "UMIDADES" da ficha CBR, extraia cbr.higroscopica da coluna "HIGROSCÓPICA" e cbr.moldagem da coluna "MOLDAGEM". Para cada uma, retorne cápsula nº, peso bruto úmido, peso bruto seco e peso/tara da cápsula.
- No quadro "CÁLCULO DA ÁGUA A JUNTAR", se houver valor para "Peso do Solo Úmido Passando na peneira nº 04", retorne em cbr.peso_solo_umido_passando_peneira_4. Não calcule se não estiver legível.
- No quadro "CÁLCULOS PARA MOLDAGEM DO C.P." ou "CÁLCULO P/ MOLDAGEM DO C.P.", extraia em cbr.calculo_moldagem os valores manuscritos de peso do solo, peso retido/passando na peneira nº 04 e água a juntar. Retorne esses pesos em gramas.
- No quadro "VERIFICAÇÃO DA MOLDAGEM", extraia em cbr.verificacao_moldagem: peso bruto do corpo de prova úmido, peso do corpo de prova úmido, densidade úmida e densidade seca, quando visíveis. Se o peso bruto aparecer como 9620 g, retorne 9620; se aparecer como 9,620 kg, retorne 9.620 e registre a unidade na evidência se possível.

GRANULOMETRIA - COMO LER
Identificação visual comum: título "GRANULOMETRIA POR PENEIRAMENTO", "PENEIRAMENTO", "PENEIRAS", "AMOSTRA TOTAL" e "AMOSTRA PARCIAL".
Campos finais necessários:
- granulometria.passante_10: na tabela de peneiramento, localize a linha "N° 10" ou "#10" ou peneira 2,0 mm. Leia a coluna "% QUE PASSA" ou "% QUE PASSA AM TOTAL" da amostra total. Não leia peso retido, peso que passa acumulado, abertura da peneira ou número da peneira.
- granulometria.passante_40: localize a linha "N° 40" ou "#40" ou peneira 0,42 mm na seção de amostra parcial. Leia a coluna "% QUE PASSA" ou "% QUE PASSA AM TOTAL". Não leia peso retido parcial.
- granulometria.passante_200: localize a linha "N° 200" ou "#200" ou peneira 0,074 mm na seção de amostra parcial. Leia a coluna "% QUE PASSA" ou "% QUE PASSA AM TOTAL". Não leia peso retido parcial.
- Em algumas fichas, as linhas N°40 e N°200 ficam abaixo da divisão "AMOSTRA PARCIAL"; ainda assim o valor esperado é percentual passante, não massa em gramas.
- Preserve casas decimais manuscritas nos passantes. Se o valor visível for 37,6, retorne 37.6; não arredonde para 38. Se for 24,5, retorne 24.5.
- Os três passantes devem estar em percentual. Valores acima de 100 são suspeitos; se a leitura parecer 139 mas deveria ser 13,9 ou 39, use warning e retorne o valor mais coerente apenas se a escrita estiver clara. Se não estiver clara, retorne null.
- Classificação TRB e SUCS: se a ficha não mostrar explicitamente, deixe null. Não calcule classificação pela granulometria.
- Limites: se a ficha ou instrução indicar que nenhum material apresentou limite, retorne "NL", "NP", "NP".

VALIDAÇÕES DE COERÊNCIA ANTES DE RESPONDER
- compactacao.umidade_otima normalmente deve ficar entre 5 e 20%.
- compactacao.densidade_maxima normalmente deve ficar entre 1.5 e 2.3 g/cm³. Se aparecer 1900 a 2200, divida por 1000.
- Em qualquer bloco de umidade, o peso bruto úmido deve ser maior ou igual ao peso bruto seco, e o peso bruto seco deve ser maior que a tara/peso da cápsula. Se a leitura violar essa ordem, trate como ilegível, retorne null para o campo suspeito e inclua warning.
- cbr.cbr normalmente deve ser percentual final. Não aceite automaticamente 70, 105, 133, 161 ou 182 quando esses números estiverem na coluna "Padrão".
- cbr.expansao normalmente deve ficar entre 0 e 10%.
- passante_10, passante_40 e passante_200 devem ficar entre 0 e 100%.
- Quando houver conflito entre resultado final destacado e tabela bruta, use o resultado final destacado e inclua warning explicando a divergência.

FORMATO DE RESPOSTA
{
  "metadata": {
    "idioma_modelo": "pt"|"en"|null,
    "tipo_esperado": "compactacao_cbr"|"granulometria"|"ambos"|"auto"|null,
    "arquivos": [
      {
        "nome": string|null,
        "tipo_detectado": "proctor"|"cbr"|"granulometria"|"desconhecido",
        "confianca": number|null,
        "observacoes": string|null
      }
    ]
  },
  "dados_comuns": {
    "interessado": string|null,
    "obra": string|null,
    "procedencia_rua": string|null,
    "cidade": string|null,
    "local_furo_estaca": string|null,
    "profundidade_furo": string|null,
    "data_ensaio": string|null,
    "registro_numero": string|null,
    "responsavel_tecnico": string|null,
    "observacoes": string|null
  },
  "proctor": {
    "energia": string|null,
    "molde_numero": string|null,
    "peso_molde_g": number|null,
    "volume_molde_cm3": number|null,
    "numero_camadas": number|null,
    "golpes_por_camada": number|null,
    "peso_soquete_g": number|null,
    "higroscopica": {
      "capsula": string|null,
      "peso_bruto_umido_g": number|null,
      "peso_bruto_seco_g": number|null,
      "tara_capsula_g": number|null
    },
    "pontos": [
      {
        "ponto": number|null,
        "peso_solo_umido_molde_g": number|null,
        "peso_solo_umido_g": number|null,
        "capsulas": [
          {
            "capsula": string|null,
            "peso_bruto_umido_g": number|null,
            "peso_bruto_seco_g": number|null,
            "tara_capsula_g": number|null
          }
        ]
      }
    ],
    "resultado_lido": {
      "umidade_otima_percent": number|null,
      "densidade_maxima_g_cm3": number|null
    }
  },
  "cbr": {
    "registro_numero_cbr": string|null,
    "molde_numero": string|null,
    "peso_molde_g": number|null,
    "volume_molde_cm3": number|null,
    "numero_camadas": number|null,
    "golpes_por_camada": number|null,
    "peso_soquete_g": number|null,
    "espessura_disco_espacador": string|null,
    "altura_cilindro_mm": number|null,
    "constante_prensa": number|null,
    "higroscopica": {
      "capsula": string|null,
      "peso_bruto_umido_g": number|null,
      "peso_bruto_seco_g": number|null,
      "tara_capsula_g": number|null
    },
    "moldagem": {
      "capsula": string|null,
      "peso_bruto_umido_g": number|null,
      "peso_bruto_seco_g": number|null,
      "tara_capsula_g": number|null
    },
    "calculo_moldagem": {
      "peso_solo_umido_passando_peneira_4_g": number|null,
      "peso_solo_seco_passando_peneira_4_g": number|null,
      "peso_pedregulho_retido_peneira_4_g": number|null
    },
    "penetracao": [
      {
        "tempo_min": number|null,
        "leitura_extensometro": number|null,
        "pressao_corrigida_kg_cm2": number|null,
        "penetracao_mm": number|null,
        "cbr_percent": number|null
      }
    ],
    "expansao": {
      "leitura_inicial_mm": number|null,
      "leitura_final_mm": number|null,
      "expansao_percent_lida": number|null
    },
    "verificacao_moldagem": {
      "peso_bruto_umido_cp_molde_kg": number|null,
      "peso_cp_umido_kg": number|null
    },
    "resultado_lido": {
      "cbr_percent": number|null,
      "expansao_percent": number|null
    }
  },
  "granulometria": {
    "empresa_executora": string|null,
    "obra": string|null,
    "procedencia_rua": string|null,
    "camada": string|null,
    "lado": string|null,
    "local_furo_estaca": string|null,
    "profundidade_furo": string|null,
    "data_ensaio": string|null,
    "laboratorio": string|null,
    "operador": string|null,
    "laboratorista": string|null,
    "registro_numero": string|null,
    "umidade": {
      "capsula": string|null,
      "peso_bruto_umido_g": number|null,
      "peso_bruto_seco_g": number|null,
      "tara_capsula_g": number|null
    },
    "amostra_total": {
      "peso_umido_total_g": number|null,
      "peso_seco_total_g": number|null,
      "material_retido_2mm_g": number|null,
      "material_passante_2mm_g": number|null
    },
    "peneiras": [
      {
        "peneira": string|null,
        "abertura_mm": number|null,
        "peso_retido_g": number|null,
        "percentual_passante": number|null
      }
    ],
    "limites": {
      "limite_liquidez": string|number|null,
      "limite_plasticidade": string|number|null,
      "indice_plasticidade": string|number|null
    },
    "classificacao_lida": {
      "trb": string|null,
      "sucs": string|null
    }
  },
  "evidencias": {
    "proctor.resultado_lido.umidade_otima_percent": string|null,
    "proctor.resultado_lido.densidade_maxima_g_cm3": string|null,
    "cbr.resultado_lido.cbr_percent": string|null,
    "cbr.resultado_lido.expansao_percent": string|null,
    "granulometria.peneiras": string|null
  },
  "warnings": []
}
""".strip()


def empty_extraction(initial: dict[str, Any] | None = None, warning: str | None = None) -> dict[str, Any]:
    initial = initial or {}
    warnings = []
    if warning:
        warnings.append(warning)
    data = {
        key: initial.get(key) or ""
        for key in [
            "interessado",
            "empresa_executora",
            "obra",
            "cidade",
            "procedencia",
            "estaca",
            "camada",
            "lado",
            "profundidade",
            "data_ensaio",
            "registro",
            "responsavel_tecnico",
            "operador",
            "laboratorista",
            "laboratorio",
            "proctor",
            "observacoes",
        ]
    }
    data.update({
        "proctor_admin": initial.get("proctor_admin") or {},
        "cbr_admin": initial.get("cbr_admin") or {},
        "granulometria_admin": initial.get("granulometria_admin") or {},
        "language": initial.get("language") or "pt",
        "test_type": initial.get("test_type") or "ambos",
        "arquivos": [],
        "compactacao": {
            "umidade_otima": None,
            "densidade_maxima": None,
            "higroscopica": {
                "capsula": None,
                "peso_bruto_umido": None,
                "peso_bruto_seco": None,
                "tara_capsula": None,
            },
            "pontos": [],
        },
        "cbr": {
            "cbr": None,
            "expansao": None,
            "higroscopica": {
                "capsula": None,
                "peso_bruto_umido": None,
                "peso_bruto_seco": None,
                "tara_capsula": None,
            },
            "moldagem": {
                "capsula": None,
                "peso_bruto_umido": None,
                "peso_bruto_seco": None,
                "tara_capsula": None,
            },
            "peso_solo_umido_passando_peneira_4": None,
            "calculo_moldagem": {
                "peso_solo_umido": None,
                "peso_retido_peneira_4": None,
                "peso_passando_peneira_4": None,
                "agua_a_juntar": None,
            },
            "verificacao_moldagem": {
                "peso_bruto_cp_umido": None,
                "peso_cp_umido": None,
                "densidade_cp_umido": None,
                "densidade_cp_seco": None,
                "peso_bruto_cp_apos_imersao": None,
                "umidade_saturacao": None,
            },
            "leituras": [],
        },
        "granulometria": {
            "passante_10": None,
            "passante_40": None,
            "passante_200": None,
            "classificacao_trb": "",
            "classificacao_sucs": "",
            "limites": {"ll": "NL", "lp": "NP", "ip": "NP"},
        },
        "warnings": warnings,
    })
    return data


def file_to_content_part(path: Path) -> dict[str, str]:
    mime_type, _ = mimetypes.guess_type(path.name)
    mime_type = mime_type or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    data_url = f"data:{mime_type};base64,{encoded}"
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return {"type": "input_file", "filename": path.name, "file_data": data_url}
    if suffix in {".jpg", ".jpeg", ".png"}:
        return {"type": "input_image", "image_url": data_url}
    raise ValueError(f"Tipo de arquivo não suportado: {path.name}")


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def infer_test_type(data: dict[str, Any], default: str = "ambos") -> str:
    if default == "auto":
        default = "ambos"
    file_items = data.get("arquivos", [])
    metadata = data.get("metadata")
    if isinstance(metadata, dict) and isinstance(metadata.get("arquivos"), list):
        file_items = [*file_items, *metadata["arquivos"]]
    classes = {
        str(item.get("classificacao") or item.get("tipo_detectado") or "").lower()
        for item in file_items
        if isinstance(item, dict)
    }
    has_compaction_cbr = bool(classes & {"compactacao", "proctor", "cbr"})
    has_granulometry = "granulometria" in classes
    if has_compaction_cbr and has_granulometry:
        return "ambos"
    if has_compaction_cbr:
        return "compactacao_cbr"
    if has_granulometry:
        return "granulometria"
    current = data.get("test_type") or data.get("expected_test_type")
    if current == "auto":
        current = default
    return current if current in {"compactacao_cbr", "granulometria", "ambos"} else default


def extracted_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def sanitize_moisture_block(data: dict[str, Any], path: tuple[str, str], label: str) -> None:
    section = data.get(path[0])
    if not isinstance(section, dict):
        return
    block = section.get(path[1])
    if not isinstance(block, dict):
        return
    wet = extracted_number(block.get("peso_bruto_umido") or block.get("peso_bruto_umido_g"))
    dry = extracted_number(block.get("peso_bruto_seco") or block.get("peso_bruto_seco_g"))
    tare = extracted_number(block.get("tara_capsula") or block.get("tara_capsula_g"))
    if wet is None and dry is None and tare is None:
        return
    if wet is None or dry is None or tare is None or wet < dry or dry < tare:
        section[path[1]] = {
            "capsula": None,
            "peso_bruto_umido": None,
            "peso_bruto_umido_g": None,
            "peso_bruto_seco": None,
            "peso_bruto_seco_g": None,
            "tara_capsula": None,
            "tara_capsula_g": None,
        }
        data.setdefault("warnings", []).append(
            f"{label} ignorada: pesos incoerentes ou incompletos."
        )


def sanitize_extracted_data(data: dict[str, Any]) -> dict[str, Any]:
    sanitize_moisture_block(data, ("proctor", "higroscopica"), "Umidade higroscópica da compactação")
    sanitize_moisture_block(data, ("compactacao", "higroscopica"), "Umidade higroscópica da compactação")
    sanitize_moisture_block(data, ("cbr", "higroscopica"), "Umidade higroscópica do CBR")
    sanitize_moisture_block(data, ("cbr", "moldagem"), "Umidade de moldagem do CBR")
    return data


def extract_data(file_paths: list[str], initial: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not settings.OPENAI_API_KEY:
        data = empty_extraction(initial, "OPENAI_API_KEY não configurada. Preencha os dados manualmente.")
        return data, None

    try:
        from openai import OpenAI
    except ImportError:
        data = empty_extraction(initial, "Pacote openai não instalado. Preencha os dados manualmente.")
        return data, None

    try:
        content: list[dict[str, str]] = [
            {"type": "input_text", "text": EXTRACTION_PROMPT},
            {
                "type": "input_text",
                "text": (
                    "Dados iniciais fornecidos pelo usuário: "
                    + json.dumps(initial or {}, ensure_ascii=False)
                ),
            },
        ]
        for file_path in file_paths:
            path = Path(file_path)
            content.append({"type": "input_text", "text": f"Arquivo enviado: {path.name}"})
            content.append(file_to_content_part(path))

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[{"role": "user", "content": content}],
        )
        raw = response.model_dump(mode="json")
        output_text = getattr(response, "output_text", "") or ""
        data = extract_json(output_text)
        base = empty_extraction(initial)
        base.update({key: value for key, value in data.items() if value is not None})
        base = sanitize_extracted_data(base)
        fallback_type = "ambos"
        if initial:
            fallback_type = initial.get("expected_test_type") or initial.get("test_type") or "ambos"
        base["test_type"] = infer_test_type(base, fallback_type)
        return base, raw
    except Exception as exc:
        data = empty_extraction(initial, f"Falha na extração com OpenAI API: {exc}")
        return data, {"error": str(exc)}
