from ensaios.services.extraction_openai import EXTRACTION_PROMPT


def test_openai_prompt_requires_new_flow_json_schema_and_nulls():
    prompt = EXTRACTION_PROMPT.lower()

    assert "metadata" in prompt
    assert "dados_comuns" in prompt
    assert "resultado_lido" in prompt
    assert "tipo_detectado" in prompt
    assert "null" in prompt
    assert "nao calcule" in prompt or "não calcule" in prompt
    assert "nao infer" in prompt or "não infer" in prompt
    assert "nao deve usar dados padrao" in prompt or "não deve usar dados padrão" in prompt


def test_openai_prompt_forbids_synthesizing_raw_tables_from_final_results():
    prompt = EXTRACTION_PROMPT.lower()

    assert "nao deve criar pontos de compactacao" in prompt or "não deve criar pontos de compactação" in prompt
    assert "nao deve sintetizar leituras de penetracao" in prompt or "não deve sintetizar leituras de penetração" in prompt
    assert "nao deve usar resultado final para preencher dados brutos" in prompt or "não deve usar resultado final para preencher dados brutos" in prompt
    assert "umidade higroscopica" in prompt or "umidade higroscópica" in prompt
    assert "moldagem" in prompt
