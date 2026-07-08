# Mapa de Células

Este mapa diferencia células de preenchimento manual e células automáticas.

As planilhas não foram coloridas nesta etapa para evitar regravação completa pelo `openpyxl`, que pode perder elementos de desenho. A distinção ficou documentada aqui de forma segura.

## Origem dos Dados

Dados preenchidos pelo usuário na interface:

- Identificação geral: interessado, empresa executora, obra, cidade, procedência/rua, local/furo/estaca, data, registro e observações.
- Identificação de amostra: camada, lado e profundidade.
- Equipe: responsável técnico, operador, laboratorista e laboratório.
- Configuração: idioma do modelo, tipo de ensaio e energia Proctor.

Dados extraídos automaticamente dos PDFs/imagens e revisados pelo usuário:

- Compactação: umidades, pesos de cápsulas, pontos da curva, umidade ótima e densidade máxima.
- CBR: umidade de moldagem, leituras de expansão, leituras de penetração, expansão final e CBR.
- Granulometria: umidade higroscópica, pesos de amostra, peneiras, percentuais passantes e classificações.
- Limites: LL, LP e IP. Quando o material não apresenta limite, usar `NL`, `NP` e `NP`.

O gerador só substitui dados administrativos nas células já existentes em cada modelo. Campos que não existem em uma ficha não são forçados na planilha.

## Compactação / CBR

Arquivo: `templates/compactacao_cbr_modelo_limpo.xlsx`

### Aba `DENS`

Preenchimento manual:

- Identificação: `B4` interessado, `F4` obra, `K4` Proctor, `M4` registro, `B5` local/estaca, `K6` profundidade, `M6` data, `B8` procedência, `F8` cidade, `J8` responsável técnico
- Umidade higroscópica: `G10:G14`
- Pontos de compactação: `C23:D27`, `F23:F27`, `I23:K27`
- Quando não houver fórmula na célula: `G25:H27`, `L25:N27`

Cálculo automático preservado:

- Umidade e médias: `G15:G17`
- Densidade úmida/seca dos pontos quando houver fórmula: `E23:E27`, `L23:N24`
- Resultados principais: `M46`, `M53`
- Aba auxiliar `Calc`, usada pela curva de compactação

### Aba `CBR`

Preenchimento manual:

- Identificação principal herdada da aba `DENS`, com `O4` recebendo o registro
- Cápsulas e umidades: `O11:P18`
- Umidade ótima quando não vinculada por fórmula: `F21`
- Dados de penetração: `F27:G32`, `J29:J32`
- Leituras de expansão: `N27`, `N29`, `N31`, `N33`
- Moldagem/verificação: `P36`, `P38`, `P40`, `P42`, `P45`, `P47`

Cálculo automático preservado:

- Dados importados da aba `DENS`
- Água a juntar: `M21:M22`, `O21:O23`, `J23`
- CBR e expansão final: `F34`, `J34`
- Verificações automáticas: `P49`, `P51`, `P56`, `P58`, `P62`

## Granulometria

Arquivo: `templates/granulometria_modelo_limpo.xlsx`

### Aba `GRANULOMEDIA `

Preenchimento manual:

- Umidade: `D3:D9`, `D11`
- Amostra total/parcial: `I3:I9`, `J9`, `K5`, `K9`, `L9`
- Peneiramento: `D19:F23`, `E19:E23`
- Identificação: `A27` obra, `D27` procedência, `H27` empresa executora, `B29` camada, `G29` local/estaca, `J29` lado, `L29` profundidade, `A31` laboratório, `C31` operador, `E31` data, `G31` laboratorista, `L31` registro

Resultados automáticos/documentados:

- Classificação TRB/SUCS: `M20`, `M21`
- Índice de grupo: `M22`
- Constantes auxiliares: `M15`, `M18`

### Aba `LIQUIDEZ`

Preenchimento manual:

- Dados do ensaio de limites, quando aplicável
- Identificação: `A22` obra, `C22` procedência, `K22` empresa executora, `A24` camada, `H24` local/estaca, `K24` lado, `L24` profundidade, `A26` laboratório, `B26` operador, `F26` data, `J26` laboratorista, `L26` registro

Resultados:

- Limite de liquidez: `M9`
- Limite de plasticidade: `M12`
- Índice de plasticidade: `M14`
